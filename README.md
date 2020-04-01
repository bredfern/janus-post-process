# OLP Post Process

This tool listens for a message in a dedicated queue indicating that a test-taker's proctored session has ended and 
the captured media should be archived. It uses the `janus-pp-rec` binary to convert MJR audio and video files captured 
from the Janus videoroom plugin into opus and webm formats respectively. It then merges these streams into a single 
webm video file. In the case that there are multiple sets of audio/video files for a session/room, it also stitches 
these media into the single archive video file.  

More information about mkvmerge can be found here [https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.option_order]


