from rest_framework import viewsets
from rest_framework.response import Response
from .models import Contact
from .serializers import ContactSerializer
from .permissions import IsOwner
from rest_framework.decorators import action
import csv, os, datetime



class ContactAPIViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    
    def get_queryset(self):
        return Contact.objects.filter(author=self.request.user)    

    @action(detail=False, methods=['GET'])
    def export_csv(self, request):
        contacts = Contact.objects.filter(author=self.request.user)
        file_path = self.get_export_file_path()
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['name', 'phone_number', 'email', 'address'])
                writer.writeheader()
                for contact in contacts: 
                    contacts_dic = {
                        'name':contact.name,
                        'phone_number': contact.phone_number,
                        'email': contact.email,
                        'address': contact.address,
                    }
                    writer.writerow(contacts_dic)
        except Exception as e:
            print(f"CSV export failed: {e}")
            
        return Response(f"Your file has been created at {file_path}")

    def get_export_file_path(self):
        '''
        Create a folder path and file name base on user's name and date.
        '''
        folder = os.path.join('contact_exports', self.request.user.username)
        os.makedirs(folder, exist_ok=True)
        filename = f"contacts_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        return os.path.join(folder, filename)
