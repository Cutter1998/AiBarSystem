$(document).ready(function() {
    // Handle form submission for placing orders
    $('form').on('submit', function(event) {
        event.preventDefault();
        var speechData = $(this).serialize(); // Serialize the form data
        $.ajax({
            url: '/process_speech', // Endpoint for processing speech
            type: 'POST',
            data: speechData, // Form data
            success: function(response) {
                $('#response').html(response); // Display the response message in the div
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
                $('#response').html('An error occurred while processing speech.');
            }
        });
    });

    // Handle voice transcription using Web Speech API
    var recognition; // Variable for Web Speech API recognition
    var isRecognizing = false; // Variable to track recognition state

    if ('webkitSpeechRecognition' in window) { // Check if Web Speech API is supported
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US'; // Set recognition language

        recognition.onstart = function() {
            isRecognizing = true;
            $('input[name="customer_speech"]').attr('placeholder', 'Listening...');
            $('input[name="customer_speech"]').removeClass('flashing');
        };

        recognition.onresult = function(event) {
            var transcript = event.results[0][0].transcript;
            $('input[name="customer_speech"]').val(transcript); // Set the transcript as the value of the input
            $('input[name="customer_speech"]').attr('placeholder', 'e.g. Hello. Please can I order one large beer?'); // Reset placeholder
        };

        recognition.onerror = function(event) {
            console.error('Recognition error:', event);
            $('input[name="customer_speech"]').attr('placeholder', 'Error occurred. Try again.');
            $('input[name="customer_speech"]').removeClass('flashing');
        };

        recognition.onend = function() {
            isRecognizing = false;
            $('input[name="customer_speech"]').attr('placeholder', 'e.g. Hello. Please can I order one large beer?');
            $('input[name="customer_speech"]').removeClass('flashing');
        };

        $('#transcribe-button').on('mousedown', function() {
            if (recognition && !isRecognizing) {
                $('input[name="customer_speech"]').val('');
                $('input[name="customer_speech"]').attr('placeholder', 'Wait...');
                $('input[name="customer_speech"]').addClass('flashing');

                // Increase the delay before starting recognition
                setTimeout(function() {
                    recognition.start(); // Start speech recognition
                }, 1); // Adjust this value to increase or decrease the delay
            }
        });

        $('#transcribe-button').on('mouseup mouseleave', function() {
            if (recognition && isRecognizing) {
                recognition.stop();
            }
        });
    } else {
        console.error('Web Speech API is not supported in this browser.');
        $('#transcribe-button').hide();
    }
});
