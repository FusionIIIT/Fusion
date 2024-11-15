from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Item, DepartmentInfo, Relationship, Event
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import Group


# Create a view for listing all items
class ItemListView(ListView):
    model = Item
    template_name = 'item_list.html'
    context_object_name = 'items'


# Create a view for viewing a single item
class ItemDetailView(DetailView):
    model = Item
    template_name = 'item_detail.html'
    context_object_name = 'item'


# Create a view for adding a new item
class ItemCreateView(CreateView):
    model = Item
    fields = ['item_name', 'quantity', 'type', 'unit', 'description']
    template_name = 'item_form.html'
    success_url = reverse_lazy('item-list')  # redirect to the list after success


# Create a view for updating an existing item
class ItemUpdateView(UpdateView):
    model = Item
    fields = ['item_name', 'quantity', 'type', 'unit', 'description']
    template_name = 'item_form.html'
    success_url = reverse_lazy('item-list')


# Create a view for deleting an item
class ItemDeleteView(DeleteView):
    model = Item
    template_name = 'item_confirm_delete.html'
    success_url = reverse_lazy('item-list')


# Create a view for listing all department information
class DepartmentInfoListView(ListView):
    model = DepartmentInfo
    template_name = 'departmentinfo_list.html'
    context_object_name = 'departments'


# Create a view for viewing a single department
class DepartmentInfoDetailView(DetailView):
    model = DepartmentInfo
    template_name = 'departmentinfo_detail.html'
    context_object_name = 'department'


# Create a view for creating a relationship between items and departments
class RelationshipCreateView(CreateView):
    model = Relationship
    fields = ['item', 'subdepartment', 'quantity']
    template_name = 'relationship_form.html'
    success_url = reverse_lazy('relationship-list')


# Create a view for listing all events
class EventListView(ListView):
    model = Event
    template_name = 'event_list.html'
    context_object_name = 'events'


# Create a view for adding a new event (Addition, Removal, Transfer)
class EventCreateView(CreateView):
    model = Event
    fields = ['event_type', 'item', 'quantity', 'in_subdepartment', 'from_subdepartment', 'responsible_user', 'remarks']
    template_name = 'event_form.html'
    success_url = reverse_lazy('event-list')


# Custom views for admin, department admin, and subdepartment admin dashboards

# Admin view - can see everything
@login_required
def admin_dashboard(request):
    if request.user.groups.filter(name='admin').exists():
        # Admin can view all items, departments, relationships, and events
        items = Item.objects.all()
        departments = DepartmentInfo.objects.all()
        relationships = Relationship.objects.all()
        events = Event.objects.all()

        return render(request, 'admin_dashboard.html', {
            'items': items,
            'departments': departments,
            'relationships': relationships,
            'events': events,
        })
    else:
        return render(request, 'access_denied.html')  # Access denied if not an admin


# Department Admin view - can see items and events in their department
@login_required
def department_admin_dashboard(request):
    if request.user.groups.filter(name='department_admin').exists():
        # Get the department for the logged-in user (department admin)
        department = DepartmentInfo.objects.filter(admin=request.user).first()

        if department:
            # Items and events related to the department
            items = Item.objects.filter(relationship__subdepartment=department)
            events = Event.objects.filter(in_subdepartment=department)

            return render(request, 'department_admin_dashboard.html', {
                'department': department,
                'items': items,
                'events': events,
            })
        else:
            return render(request, 'access_denied.html')  # Access denied if no department found
    else:
        return render(request, 'access_denied.html')  # Access denied if not a department admin


# Subdepartment Admin view - can see items and events in their subdepartment
@login_required
def subdepartment_admin_dashboard(request):
    if request.user.groups.filter(name='subdepartment_admin').exists():
        # Get the subdepartment for the logged-in user (subdepartment admin)
        subdepartment = DepartmentInfo.objects.filter(admin=request.user).first()

        if subdepartment:
            # Items and events related to the subdepartment
            items = Item.objects.filter(relationship__subdepartment=subdepartment)
            events = Event.objects.filter(in_subdepartment=subdepartment)

            return render(request, 'subdepartment_admin_dashboard.html', {
                'subdepartment': subdepartment,
                'items': items,
                'events': events,
            })
        else:
            return render(request, 'access_denied.html')  # Access denied if no subdepartment found
    else:
        return render(request, 'access_denied.html')  # Access denied if not a subdepartment admin

