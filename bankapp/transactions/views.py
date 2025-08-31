from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Transaction
from accounts.models import User

@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(
        Q(user=request.user) | Q(recipient=request.user)
    ).order_by("-timestamp")

    for t in transactions:
        t.note_decrypted = t.get_note() if t.note else ""

    return render(request, "transactions/dashboard.html", {"transactions": transactions})

@login_required
def deposit(request):
    if request.method == "POST":
        amount = int(request.POST["amount"])
        request.user.deposit(amount)
        Transaction.objects.create(user=request.user, transaction_type="DEPOSIT", amount=amount)
        return redirect("dashboard")
    return render(request, "transactions/deposit.html")

@login_required
def withdraw(request):
    if request.method == "POST":
        amount = int(request.POST["amount"])
        if request.user.withdraw(amount):
            Transaction.objects.create(user=request.user, transaction_type="WITHDRAW", amount=amount)
        return redirect("dashboard")
    return render(request, "transactions/withdraw.html")

#@csrf_exempt   #FLAW 3: CSRF disabled -- remove this whole line for fix!
@login_required
def transfer(request):
    if request.method == "POST":
        amount = int(request.POST["amount"])
        recipient_username = request.POST["recipient"]
        sender_username = request.POST["sender"]
        note = request.POST.get("note", "")

        # FLAW 1: BAC -- always use the logged-in user. remove comments below to fix
        # sender = request.user  

        try:
            recipient = User.objects.get(username=recipient_username)
            sender = User.objects.get(username=sender_username) # FLAW 1: remove this line too!
            
            if sender == recipient:
                return redirect("dashboard")
            
            if sender.withdraw(amount):
                recipient.deposit(amount)
                transaction = Transaction(
                    user=sender,
                    transaction_type="TRANSFER",
                    amount=amount,
                    recipient=recipient
                )
                transaction.set_note(note) # FLAW 4: Cryptographic failure -- fixed by encrypting the note before saving it to db
                transaction.save() 
        except User.DoesNotExist:
            pass
        return redirect("dashboard")
    return render(request, "transactions/transfer.html")
