class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Strict cache-control to prevent sensitive data from being cached
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
        response["Cross-Origin-Opener-Policy"] = "same-origin"
        response["Cross-Origin-Resource-Policy"] = "same-origin"
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Add these headers for static files too
        if "X-Content-Type-Options" not in response:
            response["X-Content-Type-Options"] = "nosniff"
        if "X-Frame-Options" not in response:
            response["X-Frame-Options"] = "DENY"
        
        # Hide Server header
        if "Server" in response:
            del response["Server"]

        response.setdefault(
            "Cross-Origin-Embedder-Policy",
            "require-corp"
        )

        return response
