from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Poll, Choice, Vote
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login
from django.contrib import messages

def index(request):
    polls = Poll.objects.all().order_by('-pub_date')
    return render(request, 'polls/index.html', {
        'polls': polls
    })
    

def register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        terms = request.POST.get('terms')

        if not terms:
            messages.error(request, "You must agree to the terms.")
            return redirect('register')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('register')

        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password1,
                first_name=full_name.split()[0] if ' ' in full_name else full_name,
                last_name=' '.join(full_name.split()[1:]) if ' ' in full_name else ''
            )
            user.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to VoteEasy.")
            return redirect('index')
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return redirect('register')

    return render(request, 'registration/register.html')

@login_required
def vote(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)

    if Vote.objects.filter(user=request.user, poll=poll).exists():
        messages.error(request, "You have already voted in this poll.")
        return redirect('results', poll_id=poll.id)
    
    if poll.is_expired:
        messages.error(request, "This poll has expired.")
        return redirect('results', poll_id=poll.id)

    if request.method == 'POST':
        selected_choice_ids = request.POST.getlist('choice')

        if not selected_choice_ids:
            messages.error(request, "Please select at least one option.")
            return render(request, 'polls/detail.html', {'poll': poll})

        if not poll.allow_multiple and len(selected_choice_ids) > 1:
            messages.error(request, "This poll allows only one choice.")
            return render(request, 'polls/detail.html', {'poll': poll})

        try:
            vote = Vote.objects.create(
                user=request.user,
                poll=poll
            )

            selected_choices = []
            for choice_id in selected_choice_ids:
                choice = get_object_or_404(Choice, id=choice_id, poll=poll)
                vote.choices.add(choice)
                choice.votes += 1
                choice.save()
                selected_choices.append(choice)

            messages.success(request, "Thank you for your vote!")
            return redirect('results', poll_id=poll.id)

        except Exception as e:
            messages.error(request, f"Error recording vote: {str(e)}")
            return render(request, 'polls/detail.html', {'poll': poll})

    # GET request → show voting form
    return render(request, 'polls/detail.html', {'poll': poll})

@login_required
def create_poll(request):
    if request.method == 'POST':
        question = request.POST.get('question')
        expires_at = request.POST.get('expires_at') or None
        allow_multiple = 'allow_multiple' in request.POST
        choice_texts = request.POST.getlist('choice_text')

        if not question:
            messages.error(request, "Poll question is required.")
            return redirect('create')

        if len([c for c in choice_texts if c.strip()]) < 2:
            messages.error(request, "You need at least two valid choices.")
            return redirect('create')

        try:
            poll = Poll.objects.create(
                question=question,
                created_by=request.user,
                expires_at=expires_at,
                allow_multiple=allow_multiple
            )

            for text in choice_texts:
                if text.strip():
                    Choice.objects.create(poll=poll, choice_text=text.strip())

            messages.success(request, "Poll created successfully!")
            return redirect('detail', poll_id=poll.id)
        except Exception as e:
            messages.error(request, f"Error creating poll: {str(e)}")

    return render(request, 'polls/create_poll.html')

@login_required
def detail(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    has_voted = Vote.objects.filter(user=request.user, poll=poll).exists()
    
    return render(request, 'polls/detail.html', {
        'poll': poll,
        'has_voted': has_voted,
    })
    
def results(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    
    total_votes = poll.total_votes
    choices_with_percent = []
    
    for choice in poll.choices.all():
        if total_votes > 0:
            percentage = round((choice.votes / total_votes) * 100, 1)
        else:
            percentage = 0.0
            
        choices_with_percent.append({
            'choice': choice,
            'percentage': percentage,
            'percentage_int': int(round(percentage))  # for width: style
        })

    context = {
        'poll': poll,
        'total_votes': total_votes,
        'choices_with_percent': choices_with_percent,
        'leading_choice': max(poll.choices.all(), key=lambda c: c.votes, default=None)
    }
    return render(request, 'polls/results.html', context)