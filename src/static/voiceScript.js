$(document).ready(function() {
  // Function to speak out the response
  function speakResponse(text) {
      if ('speechSynthesis' in window) {
          var msg = new SpeechSynthesisUtterance(text);
          msg.lang = 'en-US';
          window.speechSynthesis.speak(msg);
      } else {
          console.error('Text-to-Speech is not supported in this browser.');
      }
  }

    // Handle form submission for placing orders
    $('form').on('submit', function(event) {
        event.preventDefault();
        var orderData = $(this).serialize(); // Serialize the form data
        $.ajax({
            url: '/process_order', // Endpoint for processing order
            type: 'POST',
            data: orderData, // Form data
            success: function(response) {
                $('#response').html(response); // Display the response message in the div
                speakResponse(response); // Speak the response out loud
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
                $('#response').html('An error occurred while processing the order.');
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
            $('input[name="order"]').attr('placeholder', 'Listening...');
            $('input[name="order"]').removeClass('flashing');
        };

        recognition.onresult = function(event) {
            var transcript = event.results[0][0].transcript;
            $('input[name="order"]').val(transcript); // Set the transcript as the value of the input
            $('input[name="order"]').attr('placeholder', 'e.g. Hello. Please can I order one large beer?'); // Reset placeholder
        };

        recognition.onerror = function(event) {
            console.error('Recognition error:', event);
            $('input[name="order"]').attr('placeholder', 'Error occurred. Try again.');
            $('input[name="order"]').removeClass('flashing');
        };

        recognition.onend = function() {
            isRecognizing = false;
            $('input[name="order"]').attr('placeholder', 'e.g. Hello. Please can I order one large beer?');
            $('input[name="order"]').removeClass('flashing');
        };

        $('#transcribe-button').on('mousedown', function() {
            if (recognition && !isRecognizing) {
                $('input[name="order"]').val('');
                $('input[name="order"]').attr('placeholder', 'Wait...');
                $('input[name="order"]').addClass('flashing');

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
