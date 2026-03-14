/*!
 * # Semantic UI 2.2.12 - Rating
 * http://github.com/semantic-org/semantic-ui/
 *
 *
 * Released under the MIT license
 * http://opensource.org/licenses/MIT
 *
 */


$(document).ready(function(){
  console.log("TTTTTTTT");
});



 function sub(event)
        {
        var specific_location= $('input[name="specific_location"]').val();
        var Location = $('input[name="Location"]').val();
        var complaint_type =  $('input[name="complaint_type"]').val() ;
        var details =$('input[name="details"]').val() ;
        var myfile = $('input[name="myfile"]').val();
        if(specific_location=="" || Location=="" || details=="" || complaint_type=="")
        {
            alert("Please fill all the details!");
            return;
        }
        else
        {
            event.preventDefault();
            $.ajax({
                type : 'POST',
                url : '.',
                data : {
                    'specific_location' : specific_location,
                    'Location' : Location,
                    'complaint_type' : complaint_type,
                    'details' : details,
                    'myfile' : myfile,

                },
                success : function (data){

                    // alert("Complaint successfully lodged");
                    setTimeout(function() {
                window.location.replace('http://localhost:8000/complaint/user');
            }, 1500);

                    
                },
                error : function (data,err){
                    alert('Complaint successfully lodged ... ');

                }
            });
       }
    };

 function sub2(event)
        {
        var specific_location= $('input[name="specific_location"]').val();
        var Location = $('input[name="Location"]').val();
        var complaint_type =  $('input[name="complaint_type"]').val() ;
        var details =$('input[name="details"]').val() ;
        var myfile = $('input[name="myfile"]').val();
        if(specific_location=="" || Location=="" || details=="" || complaint_type=="")
        {
            alert("Please fill all the details!");
            return;
        }
        else
        {
            event.preventDefault();
            $.ajax({
                type : 'POST',
                url : '.',
                data : {
                    'specific_location' : specific_location,
                    'Location' : Location,
                    'complaint_type' : complaint_type,
                    'details' : details,
                    'myfile' : myfile,

                },
                success : function (data){

                    // alert("Complaint successfully lodged");
                    setTimeout(function() {
                window.location.replace('http://localhost:8000/complaint/caretaker');
            }, 1500);

                    
                },
                error : function (data,err){
                    alert('Complaint successfully lodged ... ');

                }
            });
       }
    };
 function sub3(event)
        {
        var specific_location= $('input[name="specific_location"]').val();
        var Location = $('input[name="Location"]').val();
        var complaint_type =  $('input[name="complaint_type"]').val() ;
        var details =$('input[name="details"]').val() ;
        var myfile = $('input[name="myfile"]').val();
        if(specific_location=="" || Location=="" || details=="" || complaint_type=="")
        {
            alert("Please fill all the details!");
            return;
        }
        else
        {
            event.preventDefault();
            $.ajax({
                type : 'POST',
                url : '.',
                data : {
                    'specific_location' : specific_location,
                    'Location' : Location,
                    'complaint_type' : complaint_type,
                    'details' : details,
                    'myfile' : myfile,

                },
                success : function (data){

                    // alert("Complaint successfully lodged");
                    setTimeout(function() {
                window.location.replace('http://localhost:8000/complaint/supervisor');
            }, 1500);

                    
                },
                error : function (data,err){
                    alert('Complaint successfully lodged ... ');

                }
            });
       }
    };














    









function addwork(event) {
   

   var complaint_type = $('input[name="complaint_type"]').val();
   var name = $('input[name="name"]').val();
   var str_phone_no = $('input[name="phone_no"]').val();
   var age = $('input[name="age"]').val();
   var intage = parseInt(age);
   var intpn= parseInt(str_phone_no);

    if (complaint_type == "" || name == "" || str_phone_no == "" || age == "")
    {
      alert('Please fill all the details');
      return;
    }
    else if(intpn<1999999999){
      alert('invalid phone number!');
    }

    else if (str_phone_no.length != 10){
        alert('Oops! The Phone Number Should Be Of 10 Digits');
        return;
    }
/*
    if (str_phone_no.charAt(0) !=7 || str_phone_no.charAt(0) !=8 || str_phone_no.charAt(0) !=9) {
        alert('Phone Number should begin with 9,8 or 7');
        return;
    }*/

   else if (intage < 20 || intage > 50) {
        alert("Oops! Age of the worker should be between 20 and 50.");
        return;
    }

   else
   {

    event.preventDefault();
    $.ajax({
        type: 'POST',
        url: '.',
        data: {
            'complaint_type' : complaint_type,
            'name' : name,
           // 'csrfmiddlewaretoken': csrfmiddlewaretoken,
            'phone_no' : str_phone_no,
            'age' : age,
            
        },
        success: function(data) {
            alert(" Congratulations! The Worker has been added successfully\n Please wait for confirmation");
            setTimeout(function() {
                window.location.replace('http://localhost:8000/complaint');
            }, 1500);
        },
        // error: function(data, err) {
        //     alert('Something went wrong! Please refill the form');
        //     console.log(err);
        // }
    });
  }
};





function feedsubmit()
{

   var feedback = $('input[name="feedback"]').val();
   var rating = 0;
   rating = document.getElementById("thedropdown");
  
   if (feedback == "")
   {
    alert("Please fill all the details");
    
   }
 
    else
   {
 alert(" Feedback succesfully submitted");
 
    return;
  }

}

function assignworkersubmit()
{

   var assign_worker = $('input[name="assign_worker"]').val();
  
   if (assign_worker == "")
   {
    alert("Please fill all the details");
   
   }
   else
   {
    alert("Worker successfully assigned");
   }
   /*else
   {

    $.ajax({
        type: 'POST',
        url: '.',
        data: {
          'assign_worker':assign_worker,
            
            
        },
        success: function(data) {
            alert(" Worker assigned succesfully");
           
        },
        error: function(data, err) {
            alert('Something went wrong! Please refill the form');
            console.log(err);
        }
    });
  }*/
}


function redirectsubmit()
{

   var assign_caretaker = $('input[name="assign_caretaker"]').val();
  
   if (assign_caretaker == "")
   {
    alert("Please fill all the details");
   
   }
  /* else
   {
    alert("Feedback successfully submitted");
   }*/
    else
   {

    $.ajax({
        type: 'POST',
        url: '.',
        data: {
          'assign_caretaker':assign_caretaker,
            
            
        },
        success: function(data) {
            alert(" Ccomplaint succesfully redirected");
           
        },
        // error: function(data, err) {
        //     alert('Something went wrong! Please refill the form');
        //     console.log(err);
        // }
    });
  }
}


function resolvependingsubmit()
{
  
   var yesorno = $('input[name="yesorno"]').val();
  
   if (yesorno == "")
   {
    alert("Please fill all the details");
event.preventDefault();
    }
    else
   {
            alert("Thank You for resolving the complaint");
            return;
}
}









;(function ($, window, document, undefined) {

"use strict";

window = (typeof window != 'undefined' && window.Math == Math)
  ? window
  : (typeof self != 'undefined' && self.Math == Math)
    ? self
    : Function('return this')()
;

$.fn.rating = function(parameters) {
  var
    $allModules     = $(this),
    moduleSelector  = $allModules.selector || '',

    time            = new Date().getTime(),
    performance     = [],

    query           = arguments[0],
    methodInvoked   = (typeof query == 'string'),
    queryArguments  = [].slice.call(arguments, 1),
    returnedValue
  ;
  $allModules
    .each(function() {
      var
        settings        = ( $.isPlainObject(parameters) )
          ? $.extend(true, {}, $.fn.rating.settings, parameters)
          : $.extend({}, $.fn.rating.settings),

        namespace       = settings.namespace,
        className       = settings.className,
        metadata        = settings.metadata,
        selector        = settings.selector,
        error           = settings.error,

        eventNamespace  = '.' + namespace,
        moduleNamespace = 'module-' + namespace,

        element         = this,
        instance        = $(this).data(moduleNamespace),

        $module         = $(this),
        $icon           = $module.find(selector.icon),

        initialLoad,
        module
      ;

      module = {

        initialize: function() {
          module.verbose('Initializing rating module', settings);

          if($icon.length === 0) {
            module.setup.layout();
          }

          if(settings.interactive) {
            module.enable();
          }
          else {
            module.disable();
          }
          module.set.initialLoad();
          module.set.rating( module.get.initialRating() );
          module.remove.initialLoad();
          module.instantiate();
        },

        instantiate: function() {
          module.verbose('Instantiating module', settings);
          instance = module;
          $module
            .data(moduleNamespace, module)
          ;
        },

        destroy: function() {
          module.verbose('Destroying previous instance', instance);
          module.remove.events();
          $module
            .removeData(moduleNamespace)
          ;
        },

        refresh: function() {
          $icon   = $module.find(selector.icon);
        },

        setup: {
          layout: function() {
            var
              maxRating = module.get.maxRating(),
              html      = $.fn.rating.settings.templates.icon(maxRating)
            ;
            module.debug('Generating icon html dynamically');
            $module
              .html(html)
            ;
            module.refresh();
          }
        },

        event: {
          mouseenter: function() {
            var
              $activeIcon = $(this)
            ;
            $activeIcon
              .nextAll()
                .removeClass(className.selected)
            ;
            $module
              .addClass(className.selected)
            ;
            $activeIcon
              .addClass(className.selected)
                .prevAll()
                .addClass(className.selected)
            ;
          },
          mouseleave: function() {
            $module
              .removeClass(className.selected)
            ;
            $icon
              .removeClass(className.selected)
            ;
          },
          click: function() {
            var
              $activeIcon   = $(this),
              currentRating = module.get.rating(),
              rating        = $icon.index($activeIcon) + 1,
              canClear      = (settings.clearable == 'auto')
               ? ($icon.length === 1)
               : settings.clearable
            ;
            if(canClear && currentRating == rating) {
              module.clearRating();
            }
            else {
              module.set.rating( rating );
            }
          }
        },

        clearRating: function() {
          module.debug('Clearing current rating');
          module.set.rating(0);
        },

        bind: {
          events: function() {
            module.verbose('Binding events');
            $module
              .on('mouseenter' + eventNamespace, selector.icon, module.event.mouseenter)
              .on('mouseleave' + eventNamespace, selector.icon, module.event.mouseleave)
              .on('click'      + eventNamespace, selector.icon, module.event.click)
            ;
          }
        },

        remove: {
          events: function() {
            module.verbose('Removing events');
            $module
              .off(eventNamespace)
            ;
          },
          initialLoad: function() {
            initialLoad = false;
          }
        },

        enable: function() {
          module.debug('Setting rating to interactive mode');
          module.bind.events();
          $module
            .removeClass(className.disabled)
          ;
        },

        disable: function() {
          module.debug('Setting rating to read-only mode');
          module.remove.events();
          $module
            .addClass(className.disabled)
          ;
        },

        is: {
          initialLoad: function() {
            return initialLoad;
          }
        },

        get: {
          initialRating: function() {
            if($module.data(metadata.rating) !== undefined) {
              $module.removeData(metadata.rating);
              return $module.data(metadata.rating);
            }
            return settings.initialRating;
          },
          maxRating: function() {
            if($module.data(metadata.maxRating) !== undefined) {
              $module.removeData(metadata.maxRating);
              return $module.data(metadata.maxRating);
            }
            return settings.maxRating;
          },
          rating: function() {
            var
              currentRating = $icon.filter('.' + className.active).length
            ;
            module.verbose('Current rating retrieved', currentRating);
            return currentRating;
          }
        },

        set: {
          rating: function(rating) {
            var
              ratingIndex = (rating - 1 >= 0)
                ? (rating - 1)
                : 0,
              $activeIcon = $icon.eq(ratingIndex)
            ;
            $module
              .removeClass(className.selected)
            ;
            $icon
              .removeClass(className.selected)
              .removeClass(className.active)
            ;
            if(rating > 0) {
              module.verbose('Setting current rating to', rating);
              $activeIcon
                .prevAll()
                .addBack()
                  .addClass(className.active)
              ;
            }
            if(!module.is.initialLoad()) {
              settings.onRate.call(element, rating);
            }
          },
          initialLoad: function() {
            initialLoad = true;
          }
        },

        setting: function(name, value) {
          module.debug('Changing setting', name, value);
          if( $.isPlainObject(name) ) {
            $.extend(true, settings, name);
          }
          else if(value !== undefined) {
            if($.isPlainObject(settings[name])) {
              $.extend(true, settings[name], value);
            }
            else {
              settings[name] = value;
            }
          }
          else {
            return settings[name];
          }
        },
        internal: function(name, value) {
          if( $.isPlainObject(name) ) {
            $.extend(true, module, name);
          }
          else if(value !== undefined) {
            module[name] = value;
          }
          else {
            return module[name];
          }
        },
        debug: function() {
          if(!settings.silent && settings.debug) {
            if(settings.performance) {
              module.performance.log(arguments);
            }
            else {
              module.debug = Function.prototype.bind.call(console.info, console, settings.name + ':');
              module.debug.apply(console, arguments);
            }
          }
        },
        verbose: function() {
          if(!settings.silent && settings.verbose && settings.debug) {
            if(settings.performance) {
              module.performance.log(arguments);
            }
            else {
              module.verbose = Function.prototype.bind.call(console.info, console, settings.name + ':');
              module.verbose.apply(console, arguments);
            }
          }
        },
        error: function() {
          if(!settings.silent) {
            module.error = Function.prototype.bind.call(console.error, console, settings.name + ':');
            module.error.apply(console, arguments);
          }
        },
        performance: {
          log: function(message) {
            var
              currentTime,
              executionTime,
              previousTime
            ;
            if(settings.performance) {
              currentTime   = new Date().getTime();
              previousTime  = time || currentTime;
              executionTime = currentTime - previousTime;
              time          = currentTime;
              performance.push({
                'Name'           : message[0],
                'Arguments'      : [].slice.call(message, 1) || '',
                'Element'        : element,
                'Execution Time' : executionTime
              });
            }
            clearTimeout(module.performance.timer);
            module.performance.timer = setTimeout(module.performance.display, 500);
          },
          display: function() {
            var
              title = settings.name + ':',
              totalTime = 0
            ;
            time = false;
            clearTimeout(module.performance.timer);
            $.each(performance, function(index, data) {
              totalTime += data['Execution Time'];
            });
            title += ' ' + totalTime + 'ms';
            if(moduleSelector) {
              title += ' \'' + moduleSelector + '\'';
            }
            if($allModules.length > 1) {
              title += ' ' + '(' + $allModules.length + ')';
            }
            if( (console.group !== undefined || console.table !== undefined) && performance.length > 0) {
              console.groupCollapsed(title);
              if(console.table) {
                console.table(performance);
              }
              else {
                $.each(performance, function(index, data) {
                  console.log(data['Name'] + ': ' + data['Execution Time']+'ms');
                });
              }
              console.groupEnd();
            }
            performance = [];
          }
        },
        invoke: function(query, passedArguments, context) {
          var
            object = instance,
            maxDepth,
            found,
            response
          ;
          passedArguments = passedArguments || queryArguments;
          context         = element         || context;
          if(typeof query == 'string' && object !== undefined) {
            query    = query.split(/[\. ]/);
            maxDepth = query.length - 1;
            $.each(query, function(depth, value) {
              var camelCaseValue = (depth != maxDepth)
                ? value + query[depth + 1].charAt(0).toUpperCase() + query[depth + 1].slice(1)
                : query
              ;
              if( $.isPlainObject( object[camelCaseValue] ) && (depth != maxDepth) ) {
                object = object[camelCaseValue];
              }
              else if( object[camelCaseValue] !== undefined ) {
                found = object[camelCaseValue];
                return false;
              }
              else if( $.isPlainObject( object[value] ) && (depth != maxDepth) ) {
                object = object[value];
              }
              else if( object[value] !== undefined ) {
                found = object[value];
                return false;
              }
              else {
                return false;
              }
            });
          }
          if ( $.isFunction( found ) ) {
            response = found.apply(context, passedArguments);
          }
          else if(found !== undefined) {
            response = found;
          }
          if($.isArray(returnedValue)) {
            returnedValue.push(response);
          }
          else if(returnedValue !== undefined) {
            returnedValue = [returnedValue, response];
          }
          else if(response !== undefined) {
            returnedValue = response;
          }
          return found;
        }
      };
      if(methodInvoked) {
        if(instance === undefined) {
          module.initialize();
        }
        module.invoke(query);
      }
      else {
        if(instance !== undefined) {
          instance.invoke('destroy');
        }
        module.initialize();
      }
    })
  ;

  return (returnedValue !== undefined)
    ? returnedValue
    : this
  ;
};

$.fn.rating.settings = {

  name          : 'Rating',
  namespace     : 'rating',

  slent         : false,
  debug         : false,
  verbose       : false,
  performance   : true,

  initialRating : 0,
  interactive   : true,
  maxRating     : 4,
  clearable     : 'auto',

  fireOnInit    : false,

  onRate        : function(rating){},

  error         : {
    method    : 'The method you called is not defined',
    noMaximum : 'No maximum rating specified. Cannot generate HTML automatically'
  },


  metadata: {
    rating    : 'rating',
    maxRating : 'maxRating'
  },

  className : {
    active   : 'active',
    disabled : 'disabled',
    selected : 'selected',
    loading  : 'loading'
  },

  selector  : {
    icon : '.icon'
  },

  templates: {
    icon: function(maxRating) {
      var
        icon = 1,
        html = ''
      ;
      while(icon <= maxRating) {
        html += '<i class="icon"></i>';
        icon++;
      }
      return html;
    }
  }

};

})( jQuery, window, document );


function paginate(tableId, rowsPerPage, paginationDiv) {
  var currentPage = 1;
  var tableRows = document.querySelectorAll('#' + tableId + ' tbody tr');
  var totalPages = Math.ceil(tableRows.length / rowsPerPage);

  function displayRows() {
      var startIndex = (currentPage - 1) * rowsPerPage;
      var endIndex = startIndex + rowsPerPage;
      tableRows.forEach(function (row, index) {
          if (index >= startIndex && index < endIndex) {
              row.style.display = '';
          } else {
              row.style.display = 'none';
          }
      });
  }

 function generatePagination() {
  var pagination = document.getElementById(paginationDiv);
  pagination.innerHTML = '';

  var maxPagesToShow = 5;

  // Calculate the range of pages to display
  var startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
  var endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);

  // Adjust startPage and endPage if needed
  if (endPage - startPage < maxPagesToShow - 1) {
      startPage = Math.max(1, endPage - maxPagesToShow + 1);
  }

  // Create the backward scroll button
  if (currentPage > 1) {
      pagination.appendChild(createScrollButton('<'));
  }

  // Create the page links
  for (var i = startPage; i <= endPage; i++) {
      pagination.appendChild(createPageLink(i));
  }

  // Create the forward scroll button
  if (currentPage < totalPages) {
      pagination.appendChild(createScrollButton('>'));
  }
}

function createScrollButton(label) {
  var button = document.createElement('button');
  button.textContent = label;
  button.addEventListener('click', function () {
      if (label === '<') {
          currentPage = Math.max(1, currentPage - 1);
      } else {
          currentPage = Math.min(totalPages, currentPage + 1);
      }
      displayRows();
      generatePagination();
  });
  return button;
}


  function createPageLink(pageNumber) {
      var link = document.createElement('a');
      link.href = '#';
      link.textContent = pageNumber;
      link.style.display = 'inline-block';
      link.style.padding = '5px 10px';
      link.style.marginRight = '5px';
      link.style.color = '#333';
      link.style.textDecoration = 'none';
      link.style.border = '1px solid #ccc';
      link.style.borderRadius = '3px';

      if (pageNumber === currentPage) {
          link.style.backgroundColor = '#007bff';
          link.style.color = '#fff';
      }

      link.addEventListener('click', function () {
          currentPage = parseInt(this.textContent);
          displayRows();
          generatePagination();
      });

      return link;
  }

  displayRows();
  generatePagination();
}