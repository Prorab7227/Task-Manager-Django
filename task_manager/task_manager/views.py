from django.shortcuts import render
 
 
def e_handler404(request, exception):
    return render(request, 'main_app/errors/404.html', {}, status=404)
 
 
def e_handler500(request):
    context = {"message": "Internal Server Error ERROR 500"}
    return render(request, 'main_app/errors/500.html', context, status=500)