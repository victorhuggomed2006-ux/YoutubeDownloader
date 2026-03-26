from app import app

# Para Vercel serverless
def handler(request):
    return app(request)
