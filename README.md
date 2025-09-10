# Django Contact Sync

A Django app to manage a contact list with CSV import/export functionality and cloud synchronization (e.g., Google Contacts).

## Features
- Add, edit, and delete contacts
- Import and export contacts as CSV
- Sync contacts with cloud services
- Detect duplicates and validate data


## About Me

Hi, I'm Ashkan — a junior Django developer who recently transitioned from teaching English as a second language to learning backend development.
I’m currently focused on improving my skills, building projects, and looking for opportunities to work as a backend developer.
You can find more of my work here: [My GitHub](https://github.com/AsHkAn-Django)
[Linkdin](in/ashkan-ahrari-146080150)


## How to Use
1. Clone the repository
   `git clone https://github.com/AsHkAn-Django/django-contact-sync.git`
2. Navigate into the folder
   `cd django-contact-sync`
3. Create a virtual environment and activate it
4. Install the dependencies
   `pip install -r requirements.txt`
5. Run the server
   `python manage.py runserver`


## Tutorial

search method
```python
def get_queryset(self):
   query_set = Contact.objects.filter(author=self.request.user)
   querry = self.request.GET.get('search_body')
   if querry:
      query_set = query_set.filter(Q(name__icontains=querry) |
                                    Q(phone_number__icontains=querry) |
                                    Q(email__icontains=querry) |
                                    Q(address__icontains=querry))
```

