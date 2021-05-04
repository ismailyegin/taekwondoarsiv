from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect

from sbs.Forms.UserForm import UserForm
from sbs.Forms.UserSearchForm import UserSearchForm
from accounts.models import Forgot
from sbs.models import SportClubUser, Person, Communication
from sbs.services import general_methods

from unicode_tr import unicode_tr


@login_required
def return_users(request):
    perm = general_methods.control_access(request)

    if not perm:
        logout(request)
        return redirect('accounts:login')
    users = User.objects.none()
    user_form = UserSearchForm()
    if request.method == 'POST':
        user_form = UserSearchForm(request.POST)
        if user_form.is_valid():

            firstName = unicode_tr(request.POST.get('first_name')).upper()
            lastName = unicode_tr(request.POST.get('last_name')).upper()
            email = user_form.cleaned_data.get('email')
            active = request.POST.get('is_active')
            if not (firstName or lastName or email or active):
                users = User.objects.all()
            else:
                query = Q()
                if lastName:
                    query &= Q(last_name__icontains=lastName)
                if firstName:
                    query &= Q(first_name__icontains=firstName)
                if email:
                    query &= Q(email__icontains=email)
                if active == 'True':
                    query &= Q(is_active=True)
                if active == 'False':
                    query &= Q(is_active=False)
                users = User.objects.filter(query)
    return render(request, 'kullanici/kullanicilar.html', {'users': users, 'user_form': user_form})


@login_required
def update_user(request, pk):
    user = User.objects.get(pk=pk)
    user_form = UserForm(request.POST or None, instance=user)


    if request.method == 'POST':

        if user_form.is_valid():

            user.username = user_form.cleaned_data['email']

            user.first_name = unicode_tr(user_form.cleaned_data['first_name']).upper()
            user.last_name = unicode_tr(user_form.cleaned_data['last_name']).upper()
            user.email = user_form.cleaned_data['email']

            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Kullanıcı Başarıyla Güncellendi')
            return redirect('sbs:kullanicilar')
        else:
            messages.warning(request, 'Alanları Kontrol Ediniz')

    return render(request, 'kullanici/kullanici-duzenle.html',
                  {'user_form': user_form})


@login_required
def active_user(request, pk):
    perm = general_methods.control_access(request)

    if not perm:
        logout(request)
        return redirect('accounts:login')
    if request.method == 'POST' and request.is_ajax():

        obj = User.objects.get(pk=pk)
        if obj.is_active:
            obj.is_active = False
            obj.save()
        else:
            obj.is_active = True
            obj.save()

        log = str(obj.get_full_name()) + " ->" + str(obj.is_active) + "Durumu degiştirildi "
        log = general_methods.logwrite(request, request.user, log)
        return JsonResponse({'status': 'Success', 'messages': 'save successfully'})

    else:
        return JsonResponse({'status': 'Fail', 'msg': 'Not a valid request'})



@login_required
def send_information(request, pk):
    perm = general_methods.control_access(request)

    if not perm:
        logout(request)
        return redirect('accounts:login')
    if request.method == 'POST' and request.is_ajax():

        user = User.objects.get(pk=pk)

        if not user.is_active:
            return JsonResponse({'status': 'Fail', 'msg': 'Kullanıcıyı aktifleştirin.'})
        fdk = Forgot(user=user, status=False)
        fdk.save()

        html_content = ''
        subject, from_email, to = 'Badminton Bilgi Sistemi Kullanıcı Bilgileri', 'no-reply@badminton.gov.tr', user.email
        html_content = '<h2>TÜRKİYE BADMİNTON FEDERASYONU BİLGİ SİSTEMİ</h2>'
        html_content = html_content + '<p><strong>Kullanıcı Adınız :' + str(fdk.user.username) + '</strong></p>'
        html_content = html_content + '<p> <strong>Site adresi:</strong> <a href="http://sbs.badminton.gov.tr/newpassword?query=' + str(
            fdk.uuid) + '">http://sbs.badminton.gov.tr/sbs/profil-guncelle/?query=' + str(fdk.uuid) + '</p></a>'
        msg = EmailMultiAlternatives(subject, '', from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        # password = User.objects.make_random_password()
        # obj.set_password(password)
        # # form.cleaned_data['password'] = make_password(form.cleaned_data['password'])
        # user = obj.save()
        # html_content = ''
        # subject, from_email, to = 'TWF Bilgi Sistemi Kullanıcı Bilgileri', 'no-reply@twf.gov.tr', obj.email
        # text_content = 'Aşağıda ki bilgileri kullanarak sisteme giriş yapabilirsiniz.'
        # html_content = '<p> <strong>Site adresi:</strong> <a href="http://sbs.twf.gov.tr:81"></a>sbs.twf.gov.tr:81</p>'
        # html_content = html_content + '<p><strong>Kullanıcı Adı:</strong>' + obj.username + '</p>'
        # html_content = html_content + '<p><strong>Şifre:</strong>' + password + '</p>'
        # msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        # msg.attach_alternative(html_content, "text/html")
        # msg.send()

        # print(obj.is_active)

        log = str(user.get_full_name()) + " sifre gonderildi"
        log = general_methods.logwrite(request, request.user, log)

        return JsonResponse({'status': 'Success', 'msg': 'Şifre başarıyla gönderildi'})

    else:
        return JsonResponse({'status': 'Fail', 'msg': 'Not a valid request'})
