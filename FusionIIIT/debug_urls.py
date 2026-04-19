import os
import django
import sys

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Fusion.settings.development")
django.setup()

from django.urls import get_resolver

def list_urls():
    resolver = get_resolver()
    print("Listing top-level URL patterns:")
    for pattern in resolver.url_patterns:
        print(f"  {pattern}")

    print("\nChecking for scholarships/api/ patterns:")
    for pattern in resolver.url_patterns:
        if hasattr(pattern, 'url_patterns') and 'scholarships/api/' in str(pattern):
            print(f"Found scholarships/api/ include: {pattern}")
            for sub_p in pattern.url_patterns:
                print(f"    {sub_p}")

if __name__ == "__main__":
    list_urls()
