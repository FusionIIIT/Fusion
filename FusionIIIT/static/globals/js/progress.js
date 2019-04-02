$(document).ready(function() {
    $('#example1').progress();
    $('#example2').progress();
    $('#example3').progress();
    }
);

function increment(){
    $('#example1').progress('increment');
    $('#example2').progress('increment');
    $('#example3').progress('increment');
}

function decrement() {
    $('#example1').progress('decrement');
    $('#example2').progress('decrement');
    $('#example3').progress('decrement');
}