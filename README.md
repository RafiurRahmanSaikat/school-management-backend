# School Management System — Backend

A modular Django + Django REST Framework backend for a Bangladeshi
secondary school (Class 6–10), built around the NCTB SSC subject/marks
structure. Role-based access for **Admin**, **Headteacher**, **Class
Teacher** and **Teacher**, a Bangla-unicode homepage notice board, PDF
generation for Student ID / Registration / Admit cards, and a seed script
that generates ~10,000 realistic students and ~100 teachers/staff for you
to develop and test against immediately.

## 1. Quick start

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_data        # ~10,000 students + 100 teachers, ~1 min
python manage.py runserver
```

Then visit:

- **http://127.0.0.1:8000/** — public homepage with Bangla notices
- **http://127.0.0.1:8000/admin/** — full Django admin (all models, best
  place to browse/edit everything without building a frontend)
- **http://127.0.0.1:8000/api/** — REST API (see section 5)

The seed script creates a ready-to-use superuser:

| Username | Password     | Role              |
| -------- | ------------ | ----------------- |
| `admin`  | `admin12345` | Admin (superuser) |

Every seeded teacher can also log in: username `teacher001`…`teacher100`,
password `teacher12345` for all of them. Run
`python manage.py shell -c "from apps.academics.models import Section; [print(s, s.class_teacher.user.username) for s in Section.objects.exclude(class_teacher=None)]"`
to find which teacher is the class teacher of which section.

## 2. Why it's organized this way (read this before adding a feature)

Every feature area is its own Django app under `apps/`, and each app is
self-contained: `models.py`, `admin.py`, `serializers.py`, `views.py`,
`urls.py`. The **project root `urls.py` only ever adds one `include()` line
per app** — existing apps are never touched when you add a new one.

```
apps/
  core/       # shared abstract mixins — NOT a "feature", just reusable pieces
  accounts/   # the User model — name/email/phone/address/gender/photo, ONCE
  academics/  # AcademicYear, SchoolClass (6-10), Group, Section, Subject
  teachers/   # Teacher profile (designation, subjects, qualifications...)
  students/   # Student record (guardians, roll/reg, status...)
  exams/      # Exam, MarkEntry, ExamResult + the NCTB grading/GPA engine
  billing/    # FeeCategory, Bill (due), Payment (paid)
  notices/    # Homepage notice board (Bangla unicode) + public API
  comments/   # Teacher remarks on a student
  cards/      # PDF generation: ID card / Registration card / Admit card
```

**No field is ever repeated across apps.** Every human who can log in
(admin/headteacher/teacher/staff) shares one set of "name / email / profile
picture / phone / address / gender" fields defined once, on
`apps.accounts.User` (via `apps.core.models.PersonMixin`). `Teacher` only
adds what's teaching-specific (designation, subjects, qualifications) and
links to a `User` with a `OneToOne`. `Student` is not a login account in
v1, so it declares its own copy of the shared "person" fields (via the same
`PersonMixin`) — promoting students to have their own portal login later is
a matter of adding a `Role.STUDENT` and a `OneToOne`, without touching any
other app.

Marks/GPA, bills, and comments are **not** columns on `Student` — they're
separate models with a `ForeignKey` to `Student`, so `Student` stays lean no
matter how many exams/bills/years accumulate. `StudentDetailSerializer`
(in `apps/students/serializers.py`) pulls all of it together into one API
response for "everything about this student" without the database table
itself becoming a grab-bag.

To add a brand-new feature area (e.g. "Library", "Transport", "Attendance"):

1. `python manage.py startapp library apps/library` (then fix `apps.py`'s
   `name = "apps.library"`).
2. Add `"apps.library"` to `INSTALLED_APPS` in `settings.py`.
3. Add `path("api/", include("apps.library.urls"))` in the root `urls.py`.
   No existing file needs to change beyond those two lines.

## 3. Roles & permissions

| Role                                                                    | Can do                                                                                                                                           |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Admin** / **Headteacher**                                             | Full control: every student, teacher, class, subject, bill, notice.                                                                              |
| **Class Teacher** (a `Teacher` who is set as a `Section.class_teacher`) | Full read/write access to every student**in their own section**; read-only for students in other sections they merely teach a subject in.        |
| **Teacher** (subject teacher)                                           | Read-only access to students in the section(s) they're assigned to teach; can enter/edit marks only for their own subject + section combination. |
| Money (`Bill`, `Payment`)                                               | Admin/headteacher only can create/edit; class teachers can view their own students' bills; nobody else.                                          |

All of this logic lives in **one file**: `apps/core/permissions.py`. Tighten
or loosen a rule there rather than hunting through every app's `views.py`.

## 4. NCTB grading & GPA

The exact subject/marks table you supplied is seeded verbatim in
`apps/academics/models.Subject` (code, category, CQ/MCQ/practical marks).
The grading scale and GPA formula live as **pure, dependency-free functions**
in `apps/exams/grading.py` (deliberately separate from the Django models so
they're trivial to unit test):

- 80–100 → A+ (5.00), 70–79 → A (4.00), 60–69 → A- (3.50), 50–59 → B (3.00),
  40–49 → C (2.00), 33–39 → D (1.00), 0–32 → F (0.00)
- Any core (non-4th-subject) grade of F (0.00) ⇒ overall GPA = 0.00
- 4th-subject bonus = `max(4th subject GP − 2.00, 0)`
- `GPA = (Σ core subject GPs + 4th-subject bonus) / number of core subjects`,
  capped at 5.00

> **Seed-data simplification** — the "9 core subjects" in the seed script
> are the 8 shared compulsory subjects (Bangla 1st/2nd, English 1st/2nd,
> Math, the student's own Religion subject, BGS, ICT) plus **one**
> representative subject from the student's group (Physics for Science,
> Accounting for Commerce, Geography for Arts). This is a simplification
> for demo data volume — see the docstring at the top of
> `apps/core/management/commands/seed_data.py` if your school's exact
> group-subject combination differs; only that function needs to change.
> The grading/GPA **engine itself** (`apps/exams/grading.py`) is generic and
> textbook-accurate — it just consumes whatever subject list you give it.

Recompute a student's GPA for an exam any time via
`POST /api/mark-entries/recompute/` with `{"student": <id>, "exam": <id>}`,
or the "Recompute GPA/result" action in the Django admin's Mark Entry list.

## 5. API overview

JWT auth: `POST /api/auth/token/` with `{"username", "password"}` returns
`{"access", "refresh"}`. Send `Authorization: Bearer <access>` on every
other request.

| Endpoint                                                                                    | Notes                                             |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `/api/users/`                                                                               | Accounts (admin/headteacher write, everyone read) |
| `/api/teachers/`                                                                            | Teacher profiles                                  |
| `/api/students/`                                                                            | Student records — role-scoped, see section 3      |
| `/api/classes/`, `/api/groups/`, `/api/sections/`, `/api/subjects/`, `/api/academic-years/` | Academic structure                                |
| `/api/exams/`, `/api/mark-entries/`, `/api/exam-results/`                                   | Marks & GPA                                       |
| `/api/fee-categories/`, `/api/bills/`, `/api/payments/`                                     | Billing                                           |
| `/api/notices/`                                                                             | Notice CRUD (auth'd)                              |
| `/api/public/notices/`                                                                      | Unauthenticated JSON feed, powers the homepage    |
| `/api/comments/`                                                                            | Teacher comments on a student                     |
| `/api/cards/id/<student_id>/`                                                               | Student ID card PDF                               |
| `/api/cards/registration/<student_id>/`                                                     | Registration card PDF                             |
| `/api/cards/admit/<student_id>/<exam_id>/`                                                  | Admit card PDF for an exam                        |

All list endpoints support `?search=`, pagination, and `django-filter`
query params for their listed `filterset_fields` (e.g.
`/api/students/?section__school_class=<id>&status=ACTIVE`).

## 6. Bangla notice board

`GET /` renders `templates/notices/home.html` — plain server-side HTML using
the **Noto Sans Bengali** / **Hind Siliguri** Google Fonts, so Bangla
notices display with correct typography without any extra setup. Notice
`title`/`body` are ordinary Django `TextField`s (UTF-8), so Bangla text is
stored and returned exactly as typed — no special encoding needed anywhere
in the stack. Manage notices at `/admin/notices/notice/` or via
`/api/notices/`.

If you also want Bangla text rendered _inside_ the PDF cards (not just the
homepage), see the note at the top of `apps/cards/services.py` — it needs a
bundled Bangla `.ttf` registered with ReportLab, which isn't included here
to keep the repo small.

## 7. Seed data

```bash
python manage.py seed_data                          # defaults: 10,000 students, 100 teachers
python manage.py seed_data --students 500 --teachers 20   # smaller dataset for quick testing
python manage.py seed_data --flush                   # wipe previously seeded data first, then reseed
```

What gets created:

- 1 `AcademicYear` (2026), `SchoolClass` for levels 6–10
- 4 `Group`s (Science, Commerce, Arts/Humanities, General)
- All 28 NCTB subjects with their exact marks distribution
- 18 `Section`s: Class 6–8 → General × (A, B); Class 9–10 → (Science,
  Commerce, Arts) × (A, B)
- 100 teachers/staff (mixed gender, realistic Bangladeshi names, varied
  designations, subjects, qualifications, joining dates) — one is a
  superuser `admin` account, others each have a `teacher_profile`; every
  section gets exactly one class teacher
- 10,000 students spread across all 18 sections, mixed gender, weighted
  religion distribution, guardian details, previous school, admission date,
  status, and (for Class 9–10) a chosen optional 4th subject
- Half-Yearly exam + full mark entries + computed GPA (`ExamResult`) for
  every Class 9 & 10 student, using the real grading engine
- A tuition-fee `Bill` per student with a realistic paid/partial/unpaid
  spread, and matching `Payment` rows
- 5 Bangla homepage notices, and ~300 sample teacher comments

Takes roughly 60 seconds for the full 10K/100 run on a typical laptop.

## 8. Production notes

This ships with SQLite and `DEBUG=True` for zero-friction local development.
Before deploying:

- Set `DJANGO_DEBUG=False` and a strong `DJANGO_SECRET_KEY` env var
- Point `DATABASES` at Postgres (recommended for 10K+ student rows)
- Set `DJANGO_ALLOWED_HOSTS` to your real domain(s)
- Serve `MEDIA_ROOT` (profile pictures, notice attachments) from real
  storage (S3/GCS) rather than local disk
- Put Gunicorn/uWSGI + Nginx (or similar) in front instead of
  `runserver`
