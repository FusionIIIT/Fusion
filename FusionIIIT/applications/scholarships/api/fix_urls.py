import re
with open('urls.py', 'r') as f:
    text = f.read()

text = re.sub(r"path\('mcm-applications/', views\.McmApplicationViewSet\.as_view\(\{.*?\}\), name='api-mcm-applications'\),",
    "path('mcm-applications/', views.McmApplicationViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-mcm-applications'),\n    path('mcm-applications/<int:pk>/', views.McmApplicationViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}), name='api-mcm-application-detail'),", text)

with open('urls.py', 'w') as f:
    f.write(text)
