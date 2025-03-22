document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll("a").forEach(link => {
        if (link.hostname && link.hostname !== location.hostname) {
            link.setAttribute("target", "_blank");
            link.setAttribute("rel", "noopener noreferrer");
        }
    });
});