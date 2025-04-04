from django.shortcuts import render, redirect
from .models import Crawlings
from .utils import crawl_toss_comments_by_name, get_comment_form_OpenAI

# Create your views here.
def index(request):
    company_info = request.GET.get('title')
    context = {
        'company_info': company_info,
    }
    return render(request, 'crawlings/index.html', context)

def find(request):
    if request.method == 'POST':
        stock_name = request.POST.get('title')

        # 크롤링 실행
        stock_name, code, comments = crawl_toss_comments_by_name(stock_name)

        # DB 저장
        for c in comments:
            Crawlings.objects.create(
                title = stock_name,
                code= code,
                comment=c['comment'],
            )
        
        # 3. 저장한 결과 다시 읽기
        results = Crawlings.objects.filter(title=stock_name).order_by('-updated_at')

        # 분석 결과 호출
        report = analyze_comments_by_title(stock_name)

        return render(request, 'crawlings/index.html', {
            'company_info': {
                'title': stock_name,
                'code': code,
                'comments': results,
            },
            'report': report,
        })
    else:
        return render(request, 'crawlings/index.html')

def delete_comment(request, pk):
    if request.method == 'POST':
        title = request.POST.get('title')
        comment = Crawlings.objects.get(pk=pk)
        comment.delete()

        results = Crawlings.objects.filter(title=title)
        code = results.first().code if results.exists() else '000000'
        return render(request, 'crawlings/index.html', {
            'company_info': {
                'title': title,
                'code': code,
                'comments': results,
            }
        })
    else:
        return redirect('crawlings:index')
    

def analyze_comments_by_title(title):
    comments_qs = Crawlings.objects.filter(title=title).order_by('-updated_at')
    comments = [c.comment for c in comments_qs]
    return get_comment_form_OpenAI(comments)

    
def ai_analyze(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        comments_qs = Crawlings.objects.filter(title=title).order_by('-updated_at')
        code = comments_qs.first().code if comments_qs.exists() else "000000"
        comments = [c.comment for c in comments_qs]

        report = get_comment_form_OpenAI(comments)

        return render(request, 'crawlings/index.html', {
            'company_info': {
                'title': title,
                'code': code,
                'comments': comments_qs,
            },
            'report': report
        })
    else:
        return redirect('crawlings:index')
