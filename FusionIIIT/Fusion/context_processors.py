def global_vars(request):
    return {
        'global_var': request.session.get('currentDesignationSelected', 'default_value'),
        'global_var2': request.session.get('allDesignations', 'default_value2'),
    }