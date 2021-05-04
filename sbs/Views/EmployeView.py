from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from sbs.Forms.CommunicationForm import CommunicationForm
from sbs.Forms.DirectoryCommissionForm import DirectoryCommissionForm
from sbs.Forms.DirectoryForm import DirectoryForm
from sbs.Forms.DirectoryMemberRoleForm import DirectoryMemberRoleForm
from sbs.Forms.DisabledCommunicationForm import DisabledCommunicationForm
from sbs.Forms.DisabledDirectoryForm import DisabledDirectoryForm
from sbs.Forms.DisabledPersonForm import DisabledPersonForm
from sbs.Forms.DisabledSportClubUserForm import DisabledSportClubUserForm
from sbs.Forms.DisabledUserForm import DisabledUserForm
from sbs.Forms.UserForm import UserForm
from sbs.Forms.PersonForm import PersonForm
from sbs.Forms.UserSearchForm import UserSearchForm
from sbs.models import Person, Communication
from sbs.models.DirectoryCommission import DirectoryCommission
from sbs.models.DirectoryMember import DirectoryMember
from sbs.models.DirectoryMemberRole import DirectoryMemberRole
from sbs.services import general_methods

# from zeep import Client
from sbs.models.PreRegistration import PreRegistration
from sbs.models.ReferenceReferee import ReferenceReferee
from sbs.models.ReferenceCoach import ReferenceCoach

from sbs.models.Material import Material
from sbs.Forms.MaterialForm import MaterialForm

from unicode_tr import unicode_tr

from sbs.models.Employe import Employe
from sbs.models.Abirim import Abirim
from sbs.Forms.EmployeUnitForm import EmployeUnitForm

@login_required
def return_employes(request):
    perm = general_methods.control_access(request)

    if not perm:
        logout(request)
        return redirect('accounts:login')
    members = DirectoryMember.objects.none()
    user_form = UserSearchForm()
    if request.method == 'POST':
        user_form = UserSearchForm(request.POST)
        if user_form.is_valid():
            firstName = unicode_tr(user_form.cleaned_data['first_name']).upper()
            lastName = unicode_tr(user_form.cleaned_data['last_name']).upper()
            email = user_form.cleaned_data.get('email')
            if not (firstName or lastName or email):
                members = DirectoryMember.objects.all()
            else:
                query = Q()
                if lastName:
                    query &= Q(user__last_name__icontains=lastName)
                if firstName:
                    query &= Q(user__first_name__icontains=firstName)
                if email:
                    query &= Q(user__email__icontains=email)
                members = DirectoryMember.objects.filter(query)
    return render(request, 'yonetim/kurul-uyeleri.html', {'members': members, 'user_form': user_form})

@login_required
def add_employe(request):
    perm = general_methods.control_access(request)

    if not perm:
        logout(request)
        return redirect('accounts:login')
    user_form = UserForm()
    person_form = PersonForm()
    communication_form = CommunicationForm()
    unit_form=EmployeUnitForm()
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        person_form = PersonForm(request.POST, request.FILES)
        communication_form = CommunicationForm(request.POST)
        unit_form = EmployeUnitForm(request.POST)
        # controller tc email

        mail = request.POST.get('email')
        if User.objects.filter(email=mail) or ReferenceCoach.objects.exclude(status=ReferenceCoach.DENIED).filter(
                email=mail) or ReferenceReferee.objects.exclude(status=ReferenceReferee.DENIED).filter(
            email=mail) or PreRegistration.objects.exclude(status=PreRegistration.DENIED).filter(
            email=mail):
            messages.warning(request, 'Mail adresi başka bir kullanici tarafından kullanilmaktadir.')
            return render(request, 'personel/personelEkle.html',
                          {'user_form': user_form, 'person_form': person_form,
                           'communication_form': communication_form,'unit_form':unit_form
                           })

        tc = request.POST.get('tc')
        if Person.objects.filter(tc=tc) or ReferenceCoach.objects.exclude(status=ReferenceCoach.DENIED).filter(
                tc=tc) or ReferenceReferee.objects.exclude(status=ReferenceReferee.DENIED).filter(
            tc=tc) or PreRegistration.objects.exclude(status=PreRegistration.DENIED).filter(tc=tc):
            messages.warning(request, 'Tc kimlik numarasi sistemde kayıtlıdır. ')
            return render(request, 'personel/personelEkle.html',
                          {'user_form': user_form, 'person_form': person_form,
                           'communication_form': communication_form,'unit_form':unit_form
                           })

        name = request.POST.get('first_name')
        surname = request.POST.get('last_name')
        year = request.POST.get('birthDate')
        year = year.split('/')

        # client = Client('https://tckimlik.nvi.gov.tr/Service/KPSPublic.asmx?WSDL')
        # if not (client.service.TCKimlikNoDogrula(tc, name, surname, year[2])):
        #     messages.warning(request, 'Tc kimlik numarasi ile isim  soyisim dogum yılı  bilgileri uyuşmamaktadır. ')
        #     return render(request, 'yonetim/kurul-uyesi-ekle.html',
        #                   {'user_form': user_form, 'person_form': person_form, 'communication_form': communication_form,
        #                    'member_form': member_form})

        if user_form.is_valid() and person_form.is_valid() and communication_form.is_valid():
            user = User()
            user.username = user_form.cleaned_data['email']
            user.first_name = unicode_tr(user_form.cleaned_data['first_name']).upper()
            user.last_name = unicode_tr(user_form.cleaned_data['last_name']).upper()
            user.email = user_form.cleaned_data['email']
            group = Group.objects.get(name='Yonetim')
            password = User.objects.make_random_password()
            user.set_password(password)
            user.save()
            user.groups.add(group)
            user.save()

            person = person_form.save(commit=False)
            communication = communication_form.save(commit=False)
            person.save()
            communication.save()

            employe = Employe(user=user, person=person, communication=communication)
            print(request.POST.get('birim'))
            employe.birim=Abirim.objects.get(pk=int(request.POST.get('birim')))
            employe.save()

            # subject, from_email, to = 'Halter - Yönetim/Federasyon Bilgi Sistemi Kullanıcı Giriş Bilgileri', 'no-reply@twf.gov.tr', user.email
            # text_content = 'Aşağıda ki bilgileri kullanarak sisteme giriş yapabilirsiniz.'
            # html_content = '<p> <strong>Site adresi: </strong> <a href="http://sbs.twf.gov.tr:81/"></a>sbs.twf.gov.tr:81</p>'
            # html_content = html_content + '<p><strong>Kullanıcı Adı:  </strong>' + user.username + '</p>'
            # html_content = html_content + '<p><strong>Şifre: </strong>' + password + '</p>'
            # msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            # msg.attach_alternative(html_content, "text/html")
            # msg.send()

            log = str(user.get_full_name()) + " Personel kaydedildi"
            log = general_methods.logwrite(request, request.user, log)

            messages.success(request, 'Personel Başarıyla Kayıt Edilmiştir.')

            return redirect('sbs:birim-personel-duzenle', employe.pk)

        else:

            for x in user_form.errors.as_data():
                messages.warning(request, user_form.errors[x][0])

    return render(request, 'personel/personelEkle.html',
                  {'user_form': user_form, 'person_form': person_form,
                   'communication_form': communication_form,'unit_form':unit_form
                  })


@login_required
def update_demploye(request, pk):
    perm = general_methods.control_access(request)

    if not perm:
        logout(request)
        return redirect('accounts:login')
    member = Employe.objects.get(pk=pk)
    if not member.user.groups.all():
        member.user.groups.add(Group.objects.get(name="Personel"))
        member.save()
    groups = Group.objects.all()
    user = User.objects.get(pk=member.user.pk)
    person = Person.objects.get(pk=member.person.pk)
    user_form = UserForm(request.POST or None, instance=user)
    person_form = PersonForm(request.POST or None, request.FILES or None, instance=person)
    communication = Communication.objects.get(pk=member.communication.pk)
    unit_form=EmployeUnitForm()

    if person.material:
        metarial = Material.objects.get(pk=member.person.material.pk)
    else:
        metarial = Material()
        metarial.save()
        person.material = metarial
        person.save()
    communication_form = CommunicationForm(request.POST or None, instance=communication)
    metarial_form = MaterialForm(request.POST or None, instance=metarial)
    if request.method == 'POST':

        # controller tc email

        mail = request.POST.get('email')
        if user.email != mail:
            if User.objects.filter(email=mail) or ReferenceCoach.objects.exclude(status=ReferenceCoach.DENIED).filter(
                    email=mail) or ReferenceReferee.objects.exclude(status=ReferenceReferee.DENIED).filter(
                email=mail) or PreRegistration.objects.exclude(status=PreRegistration.DENIED).filter(
                email=mail):
                messages.warning(request, 'Mail adresi başka bir kullanici tarafından kullanilmaktadir.')
                return render(request, 'personel/personelDuzenle.html',
                              {'user_form': user_form, 'communication_form': communication_form, 'member': member,
                               'person_form': person_form, 'groups': groups,'metarial_form':metarial_form,
                               'unit_form':unit_form
                               })
        tc = request.POST.get('tc')

        if person.tc != tc:
            if Person.objects.filter(tc=tc) or ReferenceCoach.objects.exclude(status=ReferenceCoach.DENIED).filter(
                    tc=tc) or ReferenceReferee.objects.exclude(status=ReferenceReferee.DENIED).filter(
                tc=tc) or PreRegistration.objects.exclude(status=PreRegistration.DENIED).filter(tc=tc):
                messages.warning(request, 'Tc kimlik numarasi sistemde kayıtlıdır. ')
                return render(request, 'personel/personelDuzenle.html',
                              {'user_form': user_form, 'communication_form': communication_form, 'member': member,
                               'person_form': person_form, 'groups': groups,'metarial_form':metarial_form,
                               'unit_form': unit_form
                               })

        name = request.POST.get('first_name')
        surname = request.POST.get('last_name')
        year = request.POST.get('birthDate')
        year = year.split('/')

        # client = Client('https://tckimlik.nvi.gov.tr/Service/KPSPublic.asmx?WSDL')
        # if not (client.service.TCKimlikNoDogrula(tc, name, surname, year[2])):
        #     messages.warning(request, 'Tc kimlik numarasi ile isim  soyisim dogum yılı  bilgileri uyuşmamaktadır. ')
        #     return render(request, 'yonetim/kurul-uyesi-duzenle.html',
        #                   {'user_form': user_form, 'communication_form': communication_form, 'member': member,
        #                    'person_form': person_form, 'member_form': member_form, 'groups': groups,
        #                    'metarial_form': metarial_form,
        #                    })

        if user_form.is_valid() and person_form.is_valid() and communication_form.is_valid() and metarial_form.is_valid():
            user_form.save()
            person_form.save()
            communication_form.save()
            metarial_form.save()
            log = str(user.get_full_name()) + " Kurul uyesi guncellendi"
            log = general_methods.logwrite(request, request.user, log)
            messages.success(request, 'Kurul Üyesi Başarıyla Güncellendi')
            # return redirect('sbs:kurul-uyeleri')
        else:
            messages.warning(request, 'Alanları Kontrol Ediniz')
    return render(request, 'personel/personelDuzenle.html',
                  {'user_form': user_form, 'communication_form': communication_form, 'member': member,
                   'person_form': person_form,  'groups': groups,'metarial_form':metarial_form,
                   'unit_form': unit_form

                   })

