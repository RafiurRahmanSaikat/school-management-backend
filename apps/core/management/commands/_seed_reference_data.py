"""
Curated reference lists used only by `manage.py seed_data`.

We hand-curate common Bangladeshi given/surnames instead of relying on a
Latin-script Bangladeshi name generator (Faker's `bn_BD` locale produces
Bangla-script names, which don't suit English-script school records/ID
cards), so seeded students/teachers/guardians look realistic in a typical
school database.
"""

MALE_FIRST_NAMES = [
    "Mohammad", "Abdul", "Rakib", "Rafiq", "Kamal", "Jamal", "Shakil", "Tanvir",
    "Rasel", "Foysal", "Imran", "Nayeem", "Saiful", "Habibur", "Mizanur",
    "Anisur", "Golam", "Shahin", "Delwar", "Rezaul", "Mahbub", "Faruk",
    "Aminul", "Zahid", "Sohel", "Emran", "Arif", "Masud", "Rubel", "Mamun",
    "Shafiqul", "Nazrul", "Iqbal", "Shamim", "Hasan", "Hossain", "Rahim",
    "Karim", "Ashraf", "Saidur", "Nasir", "Tariqul", "Fahim", "Rifat",
    "Sabbir", "Tamim", "Rayhan", "Anik", "Shuvo", "Rakibul", "Naimul",
    "Asif", "Rashed", "Sajib", "Milon", "Alamgir", "Firoz", "Selim",
    "Jubayer", "Wasim", "Kabir",
]

FEMALE_FIRST_NAMES = [
    "Fatema", "Nasrin", "Sultana", "Rehana", "Shirin", "Salma", "Ayesha",
    "Rokeya", "Nazma", "Shahida", "Rabeya", "Halima", "Marium", "Nusrat",
    "Sabina", "Taslima", "Rumana", "Farzana", "Jesmin", "Kamrun", "Shirina",
    "Rina", "Mukta", "Shathi", "Popy", "Lucky", "Moushumi", "Shampa",
    "Runa", "Dilruba", "Lipi", "Shirajum", "Munni", "Sumaiya", "Tania",
    "Jannatul", "Rupa", "Shopna", "Anika", "Israt", "Mim", "Nodi", "Priya",
    "Toma", "Trisha", "Shanta", "Puja", "Ritu", "Mitu", "Sharmin",
    "Farhana", "Sanjida", "Jui", "Sathi", "Moni", "Jhorna", "Beauty",
    "Champa", "Kanta", "Hena",
]

SURNAMES = [
    "Islam", "Rahman", "Ahmed", "Hossain", "Uddin", "Khan", "Chowdhury",
    "Miah", "Akter", "Begum", "Sarkar", "Talukder", "Bhuiyan", "Mia",
    "Molla", "Sheikh", "Haque", "Mondol", "Pramanik", "Sardar", "Munshi",
    "Biswas", "Das", "Sikder", "Kazi", "Mridha", "Gazi", "Fakir", "Patwary",
]

DISTRICTS = [
    "Dhaka", "Chattogram", "Sylhet", "Rajshahi", "Khulna", "Barishal",
    "Rangpur", "Mymensingh", "Comilla", "Narayanganj", "Gazipur", "Jessore",
    "Bogura", "Cox's Bazar", "Feni", "Noakhali", "Tangail", "Pabna",
]

PREVIOUS_SCHOOLS = [
    "Al-Amin Model Primary School", "Green View Primary School",
    "Shishu Kalyan Government Primary School", "Noor Islamia Primary School",
    "Rangpur Zilla Primary School", "City Corporation Primary School",
    "Bhuiyan Academy", "Sunrise Kindergarten & Primary School",
    "Adarsha Bidyaniketan", "Notun Din Government Primary School",
    "Moni Prima School", "Grameen Model Primary School",
]

GUARDIAN_OCCUPATIONS = [
    "Farmer", "Businessman", "School Teacher", "Government Service",
    "Private Service", "Shopkeeper", "Driver", "Tailor", "Electrician",
    "Engineer", "Doctor", "Homemaker", "Day Labourer", "Freelancer", "Imam",
]
