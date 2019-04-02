var
  where = 'client' // Adds files only to the client
;

Package.describe({
  name    : 'semantic:ui-css',
  summary : 'semantic-ui UI - CSS Release of semantic-ui UI',
  version : '2.2.9',
  git     : 'git://github.com/semantic-ui-Org/semantic-ui-UI-CSS.git',
});

Package.onUse(function(api) {

  api.versionsFrom('1.0');

  api.use('jquery', 'client');

  api.addFiles([
    // icons
    'themes/default/assets/fonts/icons.eot',
    'themes/default/assets/fonts/icons.svg',
    'themes/default/assets/fonts/icons.ttf',
    'themes/default/assets/fonts/icons.woff',
    'themes/default/assets/fonts/icons.woff2',

    // flags
    'themes/default/assets/images/flags.png',

    // release
    'semantic.css',
    'semantic.js'
  ], 'client');

});
