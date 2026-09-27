"""
Seed the database with realistic demo data.

Usage:
    python manage.py seed_data
    python manage.py seed_data --students 10000 --teachers 100
    python manage.py seed_data --flush        # wipes existing data first

Design notes:
    - Bulk inserts (bulk_create) are used everywhere volume is high (students,
      mark entries, bills) so seeding 10K+ rows takes seconds, not minutes.
      Because bulk_create bypasses each model's overridden .save() (which is
      where MarkEntry computes its grade, and Payment syncs its parent Bill),
      those derived fields are computed here in Python up-front instead and
      written directly onto the bulk-created rows.
    - GPA is only meaningfully defined by the NCTB SSC table for classes 9-10
      (this is the table the user supplied), so exams/marks/GPA are only
      generated for students in Class 9 & 10. Classes 6-8 get everything
      else (guardians, bills, comments) but no exam marks, since no marks
      table was provided for the lower classes.
    - "9 core subjects" per the supplied GPA formula = the 8 shared
      compulsory subjects (Bangla 1st/2nd, English 1st/2nd, Math, the
      student's own Religion subject, BGS, ICT) + ONE representative subject
      from the student's group (Physics for Science, Accounting for
      Commerce, Geography for Arts). The student's chosen Optional/4th
      subject (Agriculture / Home Science / Music) supplies the bonus point.
      This is a simplification for demo purposes — swap in your school's
      exact subject list in `_core_subject_codes_for_group()` below if you
      need the textbook-precise combination for your board.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.academics.models import (
    AcademicYear,
    Group,
    SchoolClass,
    Section,
    Subject,
    SubjectCategory,
)
from apps.accounts.models import Role, User
from apps.billing.models import Bill, BillStatus, FeeCategory, Payment, PaymentMethod
from apps.comments.models import TeacherComment
from apps.core.models import BloodGroup, Gender
from apps.exams.grading import grade_for_marks
from apps.exams.models import Exam, ExamResult, ExamType, MarkEntry
from apps.notices.models import Notice, NoticeCategory
from apps.students.models import GuardianRelation, Religion, Student, StudentStatus
from apps.teachers.models import Designation, Teacher

from ._seed_reference_data import (
    DISTRICTS,
    FEMALE_FIRST_NAMES,
    GUARDIAN_OCCUPATIONS,
    MALE_FIRST_NAMES,
    PREVIOUS_SCHOOLS,
    SURNAMES,
)

# --- the exact NCTB SSC subject / marks distribution table supplied ---
NCTB_SUBJECTS = [
    # (code, name, category, total, cq, mcq, practical, is_4th_candidate)
    ("101", "Bangla 1st Paper", SubjectCategory.COMPULSORY, 100, 70, 30, 0, False),
    ("102", "Bangla 2nd Paper", SubjectCategory.COMPULSORY, 100, 70, 30, 0, False),
    ("107", "English 1st Paper", SubjectCategory.COMPULSORY, 100, 100, 0, 0, False),
    ("108", "English 2nd Paper", SubjectCategory.COMPULSORY, 100, 100, 0, 0, False),
    ("109", "Mathematics", SubjectCategory.COMPULSORY, 100, 70, 30, 0, False),
    (
        "111",
        "Islam & Moral Education",
        SubjectCategory.COMPULSORY,
        100,
        70,
        30,
        0,
        False,
    ),
    (
        "112",
        "Hindu Religion & Moral Ed.",
        SubjectCategory.COMPULSORY,
        100,
        70,
        30,
        0,
        False,
    ),
    (
        "113",
        "Buddhist Religion & Moral Ed.",
        SubjectCategory.COMPULSORY,
        100,
        70,
        30,
        0,
        False,
    ),
    (
        "114",
        "Christian Religion & Moral Ed.",
        SubjectCategory.COMPULSORY,
        100,
        70,
        30,
        0,
        False,
    ),
    (
        "150",
        "Bangladesh & Global Studies (BGS)",
        SubjectCategory.COMPULSORY,
        100,
        70,
        30,
        0,
        False,
    ),
    (
        "154",
        "Information & Communication Tech (ICT)",
        SubjectCategory.COMPULSORY,
        50,
        0,
        25,
        25,
        False,
    ),
    ("136", "Physics", SubjectCategory.SCIENCE, 100, 50, 25, 25, False),
    ("137", "Chemistry", SubjectCategory.SCIENCE, 100, 50, 25, 25, False),
    ("138", "Biology", SubjectCategory.SCIENCE, 100, 50, 25, 25, False),
    ("126", "Higher Mathematics", SubjectCategory.SCIENCE, 100, 50, 25, 25, False),
    ("146", "Accounting", SubjectCategory.COMMERCE, 100, 70, 30, 0, False),
    ("152", "Finance & Banking", SubjectCategory.COMMERCE, 100, 70, 30, 0, False),
    (
        "143",
        "Business Entrepreneurship",
        SubjectCategory.COMMERCE,
        100,
        70,
        30,
        0,
        False,
    ),
    ("127", "General Science", SubjectCategory.COMMERCE, 100, 70, 30, 0, False),
    ("110", "Geography & Environment", SubjectCategory.ARTS, 100, 70, 30, 0, False),
    ("140", "Civics & Citizenship", SubjectCategory.ARTS, 100, 70, 30, 0, False),
    ("141", "Economics", SubjectCategory.ARTS, 100, 70, 30, 0, False),
    ("153", "History of BD & World Civ.", SubjectCategory.ARTS, 100, 70, 30, 0, False),
    (
        "134",
        "Agricultural Studies",
        SubjectCategory.OPTIONAL_4TH,
        100,
        50,
        25,
        25,
        True,
    ),
    ("151", "Home Science", SubjectCategory.OPTIONAL_4TH, 100, 50, 25, 25, True),
    ("149", "Music", SubjectCategory.OPTIONAL_4TH, 100, 50, 25, 25, True),
    (
        "133",
        "Physical Education & Health",
        SubjectCategory.SPECIAL,
        50,
        0,
        0,
        50,
        False,
    ),
    ("156", "Career Education", SubjectCategory.SPECIAL, 50, 0, 0, 50, False),
]

RELIGION_SUBJECT_CODE = {
    Religion.ISLAM: "111",
    Religion.HINDU: "112",
    Religion.BUDDHIST: "113",
    Religion.CHRISTIAN: "114",
    Religion.OTHER: "111",
}

GROUP_MAIN_SUBJECT_CODE = {
    "SCI": "136",  # Physics represents the Science group's core subject
    "COM": "146",  # Accounting represents the Commerce group's core subject
    "ARTS": "110",  # Geography represents the Arts group's core subject
}

COMPULSORY_CORE_CODES = [
    "101",
    "102",
    "107",
    "108",
    "109",
    "150",
    "154",
]  # + religion subject = 8


def bd_phone():
    return f"01{random.choice('3456789')}{random.randint(10000000, 99999999)}"


def random_marks(cq_max, mcq_max, practical_max, skew=0.78):
    """Marks skewed toward passing but with real spread (occasional low/F scores)."""

    def part(maximum):
        if maximum == 0:
            return Decimal("0")
        # triangular distribution: mostly good, tail of weak scores
        val = random.triangular(0, maximum, maximum * skew)
        return Decimal(str(round(val)))

    return part(cq_max), part(mcq_max), part(practical_max)


class Command(BaseCommand):
    help = "Seed the database with demo classes, subjects, teachers and students."

    def add_arguments(self, parser):
        parser.add_argument("--students", type=int, default=10000)
        parser.add_argument("--teachers", type=int, default=100)
        parser.add_argument(
            "--flush", action="store_true", help="Delete existing seeded data first."
        )

    def handle(self, *args, **options):
        n_students = options["students"]
        n_teachers = options["teachers"]

        if options["flush"]:
            self._flush()

        with transaction.atomic():
            year = self._seed_academic_year()
            classes = self._seed_classes()
            groups = self._seed_groups()
            subjects = self._seed_subjects(classes)
            sections = self._seed_sections(year, classes, groups)

        self.stdout.write(
            self.style.SUCCESS(f"Academic structure ready: {len(sections)} sections.")
        )

        with transaction.atomic():
            teachers = self._seed_teachers(n_teachers, subjects, sections)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(teachers)} teachers/staff."))

        students = self._seed_students(n_students, sections, subjects)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(students)} students."))

        self._seed_exams_and_marks(year, classes, subjects, students)
        self.stdout.write(
            self.style.SUCCESS("Seeded exams, marks and GPA results for Class 9 & 10.")
        )

        self._seed_billing(year, students)
        self.stdout.write(self.style.SUCCESS("Seeded bills and payments."))

        self._seed_notices()
        self._seed_comments(teachers, students)
        self.stdout.write(
            self.style.SUCCESS("Seeded homepage notices and teacher comments.")
        )

        self.stdout.write(
            self.style.SUCCESS(
                "\nDone. Login as admin / admin12345 at /admin/ (superuser) to explore the data."
            )
        )

    # ------------------------------------------------------------------
    def _flush(self):
        self.stdout.write("Flushing previously seeded data...")
        TeacherComment.objects.all().delete()
        Payment.objects.all().delete()
        Bill.objects.all().delete()
        MarkEntry.objects.all().delete()
        ExamResult.objects.all().delete()
        Exam.objects.all().delete()
        Notice.objects.all().delete()
        Student.objects.all().delete()
        Teacher.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Section.objects.all().delete()

    # ------------------------------------------------------------------
    def _seed_academic_year(self):
        year, _ = AcademicYear.objects.get_or_create(
            year=2026, defaults={"is_current": True}
        )
        return year

    def _seed_classes(self):
        return {
            level: SchoolClass.objects.get_or_create(level=level)[0]
            for level in range(6, 11)
        }

    def _seed_groups(self):
        data = [
            ("Science", "SCI"),
            ("Commerce", "COM"),
            ("Arts/Humanities", "ARTS"),
            ("General", "GEN"),
        ]
        return {
            code: Group.objects.get_or_create(code=code, defaults={"name": name})[0]
            for name, code in data
        }

    def _seed_subjects(self, classes):
        subjects = {}
        lower_classes = [classes[l] for l in (6, 7, 8)]
        upper_classes = [classes[l] for l in (9, 10)]
        for code, name, category, total, cq, mcq, prac, is_4th in NCTB_SUBJECTS:
            subj, _ = Subject.objects.get_or_create(
                code=code,
                defaults=dict(
                    name=name,
                    category=category,
                    total_marks=total,
                    cq_marks=cq,
                    mcq_marks=mcq,
                    practical_marks=prac,
                    is_fourth_subject_candidate=is_4th,
                ),
            )
            if category in (SubjectCategory.COMPULSORY, SubjectCategory.SPECIAL):
                subj.applicable_classes.set(lower_classes + upper_classes)
            else:
                subj.applicable_classes.set(upper_classes)
            subjects[code] = subj
        return subjects

    def _seed_sections(self, year, classes, groups):
        sections = []
        for level in (6, 7, 8):
            for name in ("A", "B"):
                sec, _ = Section.objects.get_or_create(
                    academic_year=year,
                    school_class=classes[level],
                    name=name,
                    group=groups["GEN"],
                    defaults={"capacity": 600},
                )
                sections.append(sec)
        for level in (9, 10):
            for group_code in ("SCI", "COM", "ARTS"):
                for name in ("A", "B"):
                    sec, _ = Section.objects.get_or_create(
                        academic_year=year,
                        school_class=classes[level],
                        name=name,
                        group=groups[group_code],
                        defaults={"capacity": 600},
                    )
                    sections.append(sec)
        return sections

    # ------------------------------------------------------------------
    def _seed_teachers(self, n_teachers, subjects, sections):
        subject_pool_by_category = {}
        for s in subjects.values():
            subject_pool_by_category.setdefault(s.category, []).append(s)

        designations = (
            [Designation.HEADTEACHER] * 1
            + [Designation.ASSISTANT_HEADTEACHER] * 3
            + [Designation.SENIOR_TEACHER] * 26
            + [Designation.ASSISTANT_TEACHER] * 60
            + [Designation.STAFF] * max(n_teachers - 90, 10)
        )[:n_teachers]
        random.shuffle(designations)

        teachers = []
        for i in range(1, n_teachers + 1):
            gender = random.choice([Gender.MALE, Gender.FEMALE])
            first = random.choice(
                MALE_FIRST_NAMES if gender == Gender.MALE else FEMALE_FIRST_NAMES
            )
            last = random.choice(SURNAMES)
            designation = designations[i - 1]
            role = (
                Role.HEADTEACHER
                if designation == Designation.HEADTEACHER
                else Role.TEACHER
            )
            username = f"teacher{i:03d}"

            user = User.objects.create_user(
                username=username,
                password="teacher12345",
                first_name=first,
                last_name=last,
                email=f"{username}@school.edu.bd",
                phone=bd_phone(),
                role=role,
                gender=gender,
                date_of_birth=date(
                    random.randint(1965, 1996),
                    random.randint(1, 12),
                    random.randint(1, 28),
                ),
                address_line=f"House {random.randint(1,90)}, Road {random.randint(1,20)}",
                city=random.choice(DISTRICTS),
                district=random.choice(DISTRICTS),
                is_staff=(
                    designation
                    in (Designation.HEADTEACHER, Designation.ASSISTANT_HEADTEACHER)
                ),
            )

            teacher = Teacher.objects.create(
                user=user,
                employee_id=f"EMP-{i:04d}",
                designation=designation,
                education_qualification=random.choice(
                    [
                        "M.Sc in Physics",
                        "M.A in Bangla",
                        "B.Ed",
                        "M.Sc in Mathematics",
                        "M.A in English",
                        "B.Sc in Chemistry",
                        "M.Com",
                        "M.A in Economics",
                        "Honours in Biology",
                        "Diploma in ICT",
                    ]
                ),
                joining_date=date(
                    random.randint(2005, 2025),
                    random.randint(1, 12),
                    random.randint(1, 28),
                ),
            )

            if designation != Designation.STAFF:
                categories = random.sample(
                    list(subject_pool_by_category.keys()),
                    k=min(2, len(subject_pool_by_category)),
                )
                chosen_subjects = []
                for cat in categories:
                    chosen_subjects += random.sample(
                        subject_pool_by_category[cat],
                        k=min(2, len(subject_pool_by_category[cat])),
                    )
                teacher.subjects.set(chosen_subjects)
                teacher.assigned_sections.set(
                    random.sample(sections, k=min(3, len(sections)))
                )

            teachers.append(teacher)

        # assign exactly one class teacher per section, from senior/assistant teachers
        eligible = [
            t
            for t in teachers
            if t.designation
            in (Designation.SENIOR_TEACHER, Designation.ASSISTANT_TEACHER)
        ]
        random.shuffle(eligible)
        for idx, section in enumerate(sections):
            if not eligible:
                break
            class_teacher = eligible[idx % len(eligible)]
            section.class_teacher = class_teacher
            section.save(update_fields=["class_teacher"])

        # a dedicated superuser for convenience
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                password="admin12345",
                email="admin@school.edu.bd",
                role=Role.ADMIN,
            )

        return teachers

    # ------------------------------------------------------------------
    def _seed_students(self, n_students, sections, subjects):
        optional_4th_subjects = [
            s for s in subjects.values() if s.is_fourth_subject_candidate
        ]
        religion_weights = [
            (Religion.ISLAM, 88),
            (Religion.HINDU, 8),
            (Religion.BUDDHIST, 2),
            (Religion.CHRISTIAN, 2),
        ]
        religion_pool = [r for r, w in religion_weights for _ in range(w)]

        per_section = max(n_students // len(sections), 1)
        remainder = n_students - per_section * len(sections)

        students_to_create = []
        registration_counter = 1
        blood_groups = [bg for bg in BloodGroup.values if bg]

        for si, section in enumerate(sections):
            count = per_section + (1 if si < remainder else 0)
            level = section.school_class.level
            base_age = level + 6  # rough: class 6 -> ~12yo, class 10 -> ~16yo

            for roll in range(1, count + 1):
                gender = random.choice([Gender.MALE, Gender.FEMALE])
                first = random.choice(
                    MALE_FIRST_NAMES if gender == Gender.MALE else FEMALE_FIRST_NAMES
                )
                last = random.choice(SURNAMES)
                religion = random.choice(religion_pool)

                age = base_age + random.choice([-1, 0, 0, 0, 1])
                dob = date(2026 - age, random.randint(1, 12), random.randint(1, 28))

                district = random.choice(DISTRICTS)
                father_name = f"{random.choice(MALE_FIRST_NAMES)} {last}"
                mother_name = f"{random.choice(FEMALE_FIRST_NAMES)} {last}"

                fourth_subject = None
                if section.group and section.group.code in ("SCI", "COM", "ARTS"):
                    fourth_subject = random.choice(optional_4th_subjects)

                student = Student(
                    first_name=first,
                    last_name=last,
                    gender=gender,
                    date_of_birth=dob,
                    blood_group=(
                        random.choice(blood_groups) if random.random() > 0.15 else ""
                    ),
                    religion=religion,
                    phone=bd_phone() if level >= 9 and random.random() > 0.5 else "",
                    address_line=f"Village/House {random.randint(1, 200)}, Ward {random.randint(1,15)}",
                    city=district,
                    district=district,
                    country="Bangladesh",
                    section=section,
                    roll_no=roll,
                    registration_no=f"2026{registration_counter:06d}",
                    optional_fourth_subject=fourth_subject,
                    admission_date=date(
                        2026 - (level - 6), random.randint(1, 3), random.randint(1, 28)
                    ),
                    previous_school=random.choice(PREVIOUS_SCHOOLS),
                    status=StudentStatus.ACTIVE,
                    father_name=father_name,
                    father_phone=bd_phone(),
                    father_occupation=random.choice(GUARDIAN_OCCUPATIONS),
                    mother_name=mother_name,
                    mother_phone=bd_phone(),
                    mother_occupation=random.choice(
                        ["Homemaker"] + GUARDIAN_OCCUPATIONS
                    ),
                    guardian_relation=GuardianRelation.FATHER,
                    guardian_name=father_name,
                )
                student.guardian_phone = student.father_phone
                students_to_create.append(student)
                registration_counter += 1

        created = []
        BATCH = 2000
        for i in range(0, len(students_to_create), BATCH):
            batch = students_to_create[i : i + BATCH]
            Student.objects.bulk_create(batch, batch_size=BATCH)
        # bulk_create doesn't guarantee returning usable PKs on sqlite in all
        # Django versions for further FK use in this same command, so re-fetch:
        created = list(Student.objects.all().order_by("id"))
        return created

    # ------------------------------------------------------------------
    def _seed_exams_and_marks(self, year, classes, subjects, students):
        exams_by_level = {}
        for level in (9, 10):
            exam, _ = Exam.objects.get_or_create(
                name=f"Half Yearly Exam 2026 - Class {level}",
                exam_type=ExamType.FIRST_TERM,
                academic_year=year,
                school_class=classes[level],
                defaults={"date": date(2026, 6, 15)},
            )
            exams_by_level[level] = exam

        mark_entries = []
        result_rows = (
            {}
        )  # (student_id, exam_id) -> list[grade_point, is_pass tracking done after]

        upper_students = [
            s for s in students if s.section.school_class.level in (9, 10)
        ]
        for student in upper_students:
            level = student.section.school_class.level
            exam = exams_by_level[level]
            group_code = student.section.group.code if student.section.group else None

            codes = list(COMPULSORY_CORE_CODES) + [
                RELIGION_SUBJECT_CODE[student.religion]
            ]
            if group_code in GROUP_MAIN_SUBJECT_CODE:
                codes.append(GROUP_MAIN_SUBJECT_CODE[group_code])
            if student.optional_fourth_subject_id:
                codes.append(student.optional_fourth_subject.code)

            core_grade_points = []
            for code in codes:
                subject = subjects[code]
                is_fourth = student.optional_fourth_subject_id == subject.id
                cq, mcq, prac = random_marks(
                    subject.cq_marks, subject.mcq_marks, subject.practical_marks
                )
                total = cq + mcq + prac
                grade = grade_for_marks(total, subject.total_marks)
                mark_entries.append(
                    MarkEntry(
                        exam=exam,
                        student=student,
                        subject=subject,
                        cq_obtained=cq,
                        mcq_obtained=mcq,
                        practical_obtained=prac,
                        total_obtained=total,
                        letter_grade=grade.letter_grade,
                        grade_point=grade.grade_point,
                    )
                )
                if not is_fourth:
                    core_grade_points.append(grade.grade_point)
                else:
                    fourth_gp = grade.grade_point

            has_f = any(gp == Decimal("0.00") for gp in core_grade_points)
            if has_f:
                gpa = Decimal("0.00")
            else:
                bonus = Decimal("0.00")
                if student.optional_fourth_subject_id:
                    bonus = max(fourth_gp - Decimal("2.00"), Decimal("0.00"))
                gpa = (sum(core_grade_points, Decimal("0.00")) + bonus) / Decimal(
                    len(core_grade_points)
                )
                gpa = min(gpa, Decimal("5.00")).quantize(Decimal("0.01"))

            result_rows[(student.id, exam.id)] = gpa

        BATCH = 5000
        for i in range(0, len(mark_entries), BATCH):
            MarkEntry.objects.bulk_create(mark_entries[i : i + BATCH], batch_size=BATCH)

        result_objs = [
            ExamResult(
                exam_id=exam_id,
                student_id=student_id,
                gpa=gpa,
                is_pass=gpa > Decimal("0.00"),
            )
            for (student_id, exam_id), gpa in result_rows.items()
        ]
        for i in range(0, len(result_objs), BATCH):
            ExamResult.objects.bulk_create(result_objs[i : i + BATCH], batch_size=BATCH)

    # ------------------------------------------------------------------
    def _seed_billing(self, year, students):
        category, _ = FeeCategory.objects.get_or_create(
            name="Tuition Fee", defaults={"description": "Monthly tuition fee"}
        )
        bills = []
        for student in students:
            amount_due = Decimal(random.choice([500, 600, 700, 800, 1000]))
            paid_fraction = random.choices([0, 0.5, 1], weights=[15, 25, 60])[0]
            amount_paid = (amount_due * Decimal(str(paid_fraction))).quantize(
                Decimal("1")
            )
            status = (
                BillStatus.PAID
                if paid_fraction == 1
                else (BillStatus.PARTIALLY_PAID if paid_fraction else BillStatus.UNPAID)
            )
            bills.append(
                Bill(
                    student=student,
                    category=category,
                    academic_year=year,
                    title="September 2026 Tuition Fee",
                    amount_due=amount_due,
                    amount_paid=amount_paid,
                    due_date=date(2026, 9, 10),
                    status=status,
                )
            )
        BATCH = 5000
        for i in range(0, len(bills), BATCH):
            Bill.objects.bulk_create(bills[i : i + BATCH], batch_size=BATCH)

        paid_bills = Bill.objects.filter(amount_paid__gt=0).select_related(None)
        payments = [
            Payment(
                bill=b,
                amount=b.amount_paid,
                method=random.choice(list(PaymentMethod.values)),
                paid_on=date(2026, 9, random.randint(1, 25)),
                note="Seed data payment",
            )
            for b in paid_bills.iterator(chunk_size=2000)
        ]
        for i in range(0, len(payments), BATCH):
            Payment.objects.bulk_create(payments[i : i + BATCH], batch_size=BATCH)

    # ------------------------------------------------------------------
    def _seed_notices(self):
        notices = [
            dict(
                title="বার্ষিক ক্রীড়া প্রতিযোগিতা ২০২৬",
                body="আগামী ১৫ অক্টোবর ২০২৬ তারিখে বিদ্যালয় মাঠে বার্ষিক ক্রীড়া প্রতিযোগিতা অনুষ্ঠিত হবে। সকল শিক্ষার্থীকে যথাসময়ে উপস্থিত থাকার জন্য অনুরোধ করা হলো।",
                category=NoticeCategory.GENERAL,
                pin_to_top=True,
            ),
            dict(
                title="অর্ধ-বার্ষিক পরীক্ষার সময়সূচি প্রকাশ",
                body="নবম ও দশম শ্রেণির অর্ধ-বার্ষিক পরীক্ষা আগামী ১৫ জুন ২০২৬ থেকে শুরু হবে। বিস্তারিত রুটিন নোটিশ বোর্ডে পাওয়া যাবে।",
                category=NoticeCategory.EXAM,
                pin_to_top=True,
            ),
            dict(
                title="ভর্তি বিজ্ঞপ্তি ২০২৭ শিক্ষাবর্ষ",
                body="২০২৭ শিক্ষাবর্ষে ষষ্ঠ শ্রেণিতে ভর্তির আবেদন আগামী ১ নভেম্বর থেকে শুরু হবে। আগ্রহী অভিভাবকদের অফিসে যোগাযোগ করার জন্য অনুরোধ করা হলো।",
                category=NoticeCategory.ADMISSION,
            ),
            dict(
                title="বিদ্যালয় ছুটির নোটিশ",
                body="জাতীয় ছুটির দিন উপলক্ষে আগামী ১৭ ডিসেম্বর বিদ্যালয় বন্ধ থাকবে।",
                category=NoticeCategory.HOLIDAY,
            ),
            dict(
                title="ফলাফল প্রকাশ সংক্রান্ত জরুরি বিজ্ঞপ্তি",
                body="অর্ধ-বার্ষিক পরীক্ষার ফলাফল আগামী ১০ জুলাই শ্রেণি শিক্ষকের মাধ্যমে জানিয়ে দেওয়া হবে।",
                category=NoticeCategory.RESULT,
            ),
        ]
        admin_user = User.objects.filter(username="admin").first()
        for n in notices:
            Notice.objects.get_or_create(
                title=n["title"], defaults={**n, "published_by": admin_user}
            )

    def _seed_comments(self, teachers, students):
        class_teachers = [t for t in teachers if t.is_class_teacher]
        if not class_teachers:
            return
        sample_students = random.sample(students, k=min(300, len(students)))
        remarks = [
            "Shows consistent improvement in class participation.",
            "Needs to focus more on regular homework completion.",
            "Excellent performance in class tests this term.",
            "Should improve attendance and punctuality.",
            "Very cooperative and disciplined in class.",
            "Struggling with Mathematics; recommend extra support.",
            "Active participation in co-curricular activities.",
        ]
        comments = []
        for student in sample_students:
            teacher = student.section.class_teacher or random.choice(class_teachers)
            comments.append(
                TeacherComment(
                    student=student,
                    teacher=teacher,
                    comment=random.choice(remarks),
                )
            )
        TeacherComment.objects.bulk_create(comments, batch_size=1000)
