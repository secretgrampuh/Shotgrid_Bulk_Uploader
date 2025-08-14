This script was for the day-to-day on Adult Swim's Yule Log and Yule Log 2. It could upload and distribute new work from overseas vendors, create new playlist from the Adult Swim editor, and create new playlists from in-house artists to send back to Adult Swim. All handled in one CLI tool with multiple arguments.

This will upload both proxies and shots to SG. It avoids things from the exports folder and files that end in _source

Arguments:
--new_sequence : This is used for exporting a new sequence from Phil
--proxies: This is used for uploading new proxies
--review: This is used for sending deliveries from Media Team Folder (Studio)
--purple: This is used for sending deliveries from Purple Patch Folder (Vendor)

--playlist: Enter playlist name
--target: The target folder for uploads. This only works in conjunction with --new sequence though

python /Users/mtimac2/Documents/Develop/Shotgun_Upload_Versions.py --new_sequence --target "/Volumes/Branching Out EDIT/Branching Out/VFX/YL2_025_COVR" --playlist "20240828_YL2_025_COVR_Plates"

python /Users/mtimac2/Documents/Develop/Shotgun_Upload_Versions.py --review --playlist "20241015_MediaTeam"


Sample usage: /Users/mtimac2/Documents/Develop/Shotgun_Upload_Versions.py /path/to/target/folder playlist_name



