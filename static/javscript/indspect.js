  document.addEventListener('contextmenu', function (e) {
          e.preventDefault();
        });
      
        // Disable F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+U
        document.addEventListener('keydown', function (e) {
          if (
            e.key === "F12" || 
            (e.ctrlKey && e.shiftKey && (e.key === "I" || e.key === "J")) || 
            (e.ctrlKey && e.key === "U") || 
            (e.ctrlKey && e.shiftKey && e.key === "C")
          ) {
            e.preventDefault();
          }
        });