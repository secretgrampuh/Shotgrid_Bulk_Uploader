import pprint # Useful for debugging
import shotgun_api3
from glob import glob
import os
import shutil
import subprocess
import time
import sys
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips
from pathlib import Path
import json
from datetime import datetime


###########
###     This will upload both proxies and shots to SG. It avoids things from the exports folder and files that end in _source

####    Arguments:
#       --new_sequence : This is used for exporting a new sequence from Phil
# #     --proxies: This is used for uploading new proxies
#       --review: This is used for sending deliveries from Media Team Folder
#       --purple: This is used for sending deliveries from Purple Patch Folder

#       --playlist: Enter playlist name
#       --target: The target folder for uploads. This only works in conjunction with --new sequence though

###     python /Users/mtimac2/Documents/Develop/Shotgun_Upload_Versions.py --new_sequence --target "/Volumes/Branching Out EDIT/Branching Out/VFX/YL2_025_COVR" --playlist "20240828_YL2_025_COVR_Plates"

###     python /Users/mtimac2/Documents/Develop/Shotgun_Upload_Versions.py --review --playlist "20241015_MediaTeam"


###     Sample usage /Users/mtimac2/Documents/Develop/Shotgun_Upload_Versions.py /path/to/target/folder playlist_name
###########


SERVER_PATH = "https://mediateam.shotgrid.autodesk.com/"
SCRIPT_NAME = 'python_script'
SCRIPT_KEY = 'python_key'

global sg
sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
global USER_ID
USER_ID=88

branching_filters = [['project', 'is', {'type': 'Project', 'id':122}]]
branching_fields = [
    'id',
    'code',
    'entity',
    'description',
    'playlists',
    'step_0',
    'name',
    'sg_task',
    'sg_uploaded_movie',
    'status',
    'Status',
    'Level',
    'Phase',
    'open_notes',
    'attachments',
    'sg_status_list',
    'sg_first_frame',
    'step',
    'tasks',
]

proxy_timecode_dict={}
errorFiles=[]
didnt_make_it=[]
full_version_dict={}
full_shot_dict={}
full_sequence_dict={}

tasks_to_update_dict={}

Branching_sequences = ['YL2_010_POLI',
                       'YL2_020_ZOOM',
                       'YL2_030_LOG1',
                       'YL2_040_LOG2',
                       'YL2_050_REST',
                       'YL2_060_HELI',
                       'YL2_070_LOG3',
                       'YL2_080_TRAU',
                       'YL2_090_SNTA',
                       'YL2_100_SPLN',
                       'YL2_110_FREZ',
                       'YL2_120_LEAF',
                       'YL2_130_NANA',
                       'YL2_140_FLEE',
                       'YL2_150_FEST',
                       'YL2_160_MULT',
                       'YL2_170_BOSS',
                       'YL2_180_FALL',
                       'YL2_190_BBRD',
                       'YL2_200_FINL']

Refernce_mock_json_file_path = r'/Users/mtimac2/Documents/Develop/z_Logs/Reference_Mock_Paths_Dict.json'

with open(Refernce_mock_json_file_path, 'r') as json_file:
    all_reference_mock_dict = json.load(json_file)


def create_movie_from_still(image_path):
    shotcode=os.path.basename(image_path)[:19]
    if shotcode in all_reference_mock_dict.keys():
        video_path=all_reference_mock_dict[shotcode]
        output_video_path=str(Path(image_path).with_suffix('.mp4'))#.replace('.mp4','_video.mp4')
        if not os.path.exists(output_video_path):
            fps = 23.978  # Frames per second
            extra_frames = 12  # Number of extra frames at the beginning and end

            # Step 1: Load the original video and extract the audio
            video_clip = VideoFileClip(video_path)
            audio_clip = video_clip.audio

            # Step 2: Create the still image clip
            image_clip = ImageClip(image_path, duration=video_clip.duration)

            # Step 3: Create silent clips at the beginning and end
            silence_duration = extra_frames / fps
            start_silence_clip = ImageClip(image_path, duration=silence_duration)
            end_silence_clip = ImageClip(image_path, duration=silence_duration)

            # Step 4: Combine the clips: silence + video with audio + silence
            final_clip = concatenate_videoclips([start_silence_clip, image_clip.set_audio(audio_clip), end_silence_clip])

            # Step 5: Set the frame rate
            final_clip = final_clip.set_fps(fps)

            # Step 6: Write the result to a file
            final_clip.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

            # Step 7: Close the clips
            video_clip.close()
            audio_clip.close()
            image_clip.close()

        print(f"Final video with extra frames saved as {output_video_path}")
    else:
        leftover_image_files.append(image_path)

def Shotgun_Find_All_Tasks():
    filters = [['project', 'is', {'type': 'Project', 'id':122}]]
    fields = [
        'id',
        'code',
        'entity'
    ]
    filter_presets = [ {
        'preset_name': 'LATEST',
        'latest_by': 'ENTITIES_CREATED_AT'
    } ]
    sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
    search_tasks = sg.find('Task', filters, fields)
    return search_tasks

def Shotgun_Find_All_Sequences():
    filters = [['project', 'is', {'type': 'Project', 'id':122}]]
    fields = [
        'id',
        'code',
        'entity'
    ]
    filter_presets = [ {
        'preset_name': 'LATEST',
        'latest_by': 'ENTITIES_CREATED_AT'
    } ]
    sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
    search_sequences = sg.find('Sequence', filters, fields)
    all_current_sequences = []
    all_current_sequences_dict = {}
    for sequence in search_sequences:
        sequence_name = sequence['code']
        if sequence_name in all_current_sequences:
            print(f"{sequence_name} in all_current_sequences more than once!")
            time.sleep(3)
        if sequence_name not in all_current_sequences:
            all_current_sequences.append(sequence_name)
            all_current_sequences_dict[sequence_name] = sequence['id']
    return all_current_sequences_dict

def Shotgun_Find_All_Shots():
    filters = [['project', 'is', {'type': 'Project', 'id':122}]]
    fields = [
        'id',
        'code',
        'entity'
    ]
    filter_presets = [ {
        'preset_name': 'LATEST',
        'latest_by': 'ENTITIES_CREATED_AT'
    } ]
    sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
    search_shots = sg.find('Shot', filters, fields)
    all_current_shots = []
    all_current_shots_dict = {}
    for shot in search_shots:
        shot_name = shot['code']
        if shot_name in all_current_shots:
            print(f"{shot_name} in all_current_shots more than once!")
            time.sleep(3)
        if shot_name not in all_current_shots:
            all_current_shots.append(shot_name)
            all_current_shots_dict[shot_name] = shot['id']
    return all_current_shots_dict

def Shotgun_Find_All_Versions():
    filters = [['project', 'is', {'type': 'Project', 'id':122}]]
    fields = [
        'id',
        'code',
        'entity',
        'sg_first_frame'
    ]
    filter_presets = [ {
        'preset_name': 'LATEST',
        'latest_by': 'ENTITIES_CREATED_AT'
    } ]
    sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
    search_versions = sg.find('Version', filters, fields)
    all_current_versions = []
    all_current_versions_dict = {}
    for version in search_versions:
        version_name = version['code']
        full_version_dict[version_name]=version
        if version_name in all_current_versions:
            print(f"{version_name} in all_current_sequences more than once!")
            time.sleep(3)
        if version_name not in all_current_versions:
            all_current_versions.append(version_name)
            all_current_versions_dict[version_name] = version['id']
    return all_current_versions_dict

def Shotgun_Find_All_Playlists():
    filters = [['project', 'is', {'type': 'Project', 'id':122}]]
    fields = [
        'id',
        'code',
        'entity'
    ]
    filter_presets = [ {
        'preset_name': 'LATEST',
        'latest_by': 'ENTITIES_CREATED_AT'
    } ]
    sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
    search_playlists = sg.find('Playlist', filters, fields)
    all_current_playlists = []
    all_current_playlists_dict = {}
    for playlist in search_playlists:
        playlistName = playlist['code']
        if playlistName in all_current_playlists:
            errorFiles[playlistName] = "appears more than once on Shotgrid!"
            print(f"{playlistName} appears more than once on Shotgrid!")
        if playlistName not in all_current_playlists:
            all_current_playlists.append(playlistName)
            all_current_playlists_dict[playlistName] = playlist['id']
    return all_current_playlists_dict

def Shotgun_Find_All_Playlists():
    filters = [['project', 'is', {'type': 'Project', 'id':122}]]
    fields = [
        'id',
        'code',
        'entity'
    ]
    filter_presets = [ {
        'preset_name': 'LATEST',
        'latest_by': 'ENTITIES_CREATED_AT'
    } ]
    sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
    search_playlists = sg.find('Playlist', filters, fields)
    all_current_playlists = []
    all_current_playlists_dict = {}
    for playlist in search_playlists:
        playlistName = playlist['code']
        if playlistName in all_current_playlists:
            errorFiles[playlistName] = "appears more than once on Shotgrid!"
            print(f"{playlistName} appears more than once on Shotgrid!")
        if playlistName not in all_current_playlists:
            all_current_playlists.append(playlistName)
            all_current_playlists_dict[playlistName] = playlist['id']
    return all_current_playlists_dict

def Create_Playlist(PlaylistName):
    all_current_playlists_dict = Shotgun_Find_All_Playlists()
    if PlaylistName in all_current_playlists_dict:
        playlistID = all_current_playlists_dict[PlaylistName]
    else:
        data = {'project':{"type":"Project","id":122},'code': PlaylistName}
        sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
        result = sg.create('Playlist',data)
        playlistID = result['id']
        print(f"Created new playlist on Shotgrid named {PlaylistName}. Uploading shortly...")
    Playlist_Data = [{'id':playlistID, 'name': PlaylistName, 'type': 'Playlist'}]
    return Playlist_Data

def check_for_dupes(versionCode,playlistName):
    dupeCheck=False
    filters = [['project', 'is', {'type': 'Project', 'id':122}],['code','is',versionCode]]
    fields = [
        'id',
        'code',
        'entity',
        'playlists'
    ]
    filter_presets = [ {
        'preset_name': 'LATEST',
        'latest_by': 'ENTITIES_CREATED_AT'
    } ]
    sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
    results = sg.find('Version', filters, fields)
    for shot in results:
        for playlist in shot['playlists']:
            if playlist['name']==playlistName:
                dupeCheck=True
    return dupeCheck

def Quick_ParseCode(item):
    versionName = os.path.basename(item)
    if "_sh" not in versionName.lower():
        try:
            ShotCode=versionName.split(".")[0]
            errorFiles[ShotCode]=f"{ShotCode} has at least one instance of no _Sh token in filename"
            return "error","error"
        except:
            errorFiles[versionName]=f"{versionName} has at least one instance of no _Sh token in filename, also no period for extension type"
            return "error","error"
    else:
        SeqCode = versionName.split("_Sh")[0]
        if "YL2_" not in SeqCode:
            ShotCode = SeqCode+"_Sh"+(versionName.split("_Sh")[1]).split("_")[0].split(".")[0]
            errorFiles[ShotCode]=f"No YL2_ token in {ShotCode}"
            return "error","error"
        else:
            SeqCode = "YL2_"+(versionName.split("YL2_")[1]).split("_Sh")[0]
            ShotCode = SeqCode+"_Sh"+(versionName.split("_Sh")[1]).split("_")[0].split(".")[0]
            return SeqCode, ShotCode


def get_start_timecode(proxy):
    command=[f'exiftool',f'{proxy}']
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        # Access the output as a string
        output = result.stdout
        if 'Start Timecode      ' in output:
            start_timecode=output.split('Start Timecode      ')[1].split(': ')[1].split('\n')[0]
        else:
            start_timecode='11:11:11:11'
    return start_timecode

def create_sequence(sequence_name):
    data = {'project':{"type":"Project","id":122},'code': sequence_name}
    sequence_info = sg.create('Sequence', data)
    print(f'successfully created Sequence entity for: {sequence_name}')
    full_sequence_dict[sequence_name]=sequence_info
    all_sequences[sequence_name]=sequence_info['id']
    return sequence_info

def create_shot(version_name,start_timecode,sequence_name,sequence_id):
    # return
    if "_sh0" in version_name.lower() or "_sh1" in version_name.lower():
        data={'project':{"type":"Project","id":122},
            'code': version_name,
            'sg_sequence':{'id': sequence_id, 'name': sequence_name, 'type': 'Sequence'},
            'task_template': {'id': 46,
                    'name': 'BranchingOut_Template',
                    'type': 'TaskTemplate'},
            'sg_tc_start':start_timecode}
    else:
        sequence_name="zRAW_SHOTS"
        data = {'project':{"type":"Project","id":122},
            'code': version_name,
            'sg_sequence':{'id': sequence_id, 'name': sequence_name, 'type': 'Sequence'},
            'sg_tc_start':start_timecode}
            # 'user': {'type': 'HumanUser', 'id':88} }

    shot_info=sg.create('Shot',data)
    print(f'successfully created Shot entity for: {version_name}')
    full_shot_dict[version_name]=shot_info
    all_shots[version_name]=shot_info['id']
    return shot_info

def Shotgun_Find_One_Task(id_to_search):
    filters = [['project', 'is', {'type': 'Project', 'id':122}],
               ["entity", "is", {"type": "Shot", "id": id_to_search}]]
    sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
    search_tasks = sg.find('Task', filters, branching_fields)
    return search_tasks

def set_task_status(version_name,Shot_ID):
    status='ip'
    if 'roto' in version_name.lower():
        task_type='Roto'
    if 'anim' in version_name.lower():
        task_type='Animation'
    elif 'paint' in version_name.lower():
        task_type='Roto'
    elif 'comp' in version_name.lower():
        task_type='Comp'
    elif 'final' in version_name.lower():
        task_type='Comp'
    elif 'reference' in version_name.lower():
        task_type='Plate Online'
        status='apr'
    elif 'layout' in version_name.lower():
        task_type='Layout'
        # print('made it this far 1')
    elif 'tracking' in version_name.lower():
        task_type='Tracking'
    elif 'model' in version_name.lower():
        task_type='Tracking'
            # return [task_type,status]
    possible_tasks=Shotgun_Find_One_Task(Shot_ID)
    # print('made it this far 2')

    for task in possible_tasks:
        if task['step']['name']==task_type:
            task_id=task['id']
            data={'sg_status_list':status}
            sg.update('Task',task_id,data)
            # print('made it this far 3')
            return task_id
        


def CreateVersion(versionName,start_timecode,playlist_id,proxy,Shot_ID="",TaskID="",):
    print(f"Creating Version: {versionName}")
    version_path_to_frames=os.path.dirname(proxy)
    if '_sh0' in versionName.lower() or '_sh1' in versionName.lower():
        SeqCode,ShotCode=Quick_ParseCode(versionName)
        print(versionName,SeqCode)
        print('station 1')
        version_path_to_frames = rf'/Volumes/Branching Out EDIT/Branching Out/VFX/{SeqCode}/{ShotCode}/Source'
    data = { 'project': {'type': 'Project','id': 122},
         'code': versionName,
         'sg_tc_start':start_timecode,
        #  'playlists': [{'id': playlist_id, 'name': playlist_name, 'type': 'Playlist'}],
         'sg_path_to_frames': version_path_to_frames,
         'user': {'type': 'HumanUser', 'id': USER_ID} }
    if '_mock' in versionName.lower():
        data['sg_first_frame']=1013
        data['playlists']=[{'id': playlist_id, 'name': playlist_name, 'type': 'Playlist'}]
    elif '_sh' in versionName.lower():
        data['sg_first_frame']=1001
        data['playlists']=[{'id': playlist_id, 'name': playlist_name, 'type': 'Playlist'}]
    else:
        first_frame=timecode_to_frames(proxy_timecode_dict[versionName])
        data['sg_first_frame']=first_frame

    if Shot_ID != "":
        data['entity']= {'type': 'Shot', 'id': Shot_ID}
    TaskID=set_task_status(versionName,Shot_ID)
    print(TaskID)
    if TaskID != None:
        data['sg_task']= {'type': 'Task', 'id': TaskID}



    sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
    result = sg.create('Version', data)
    print(f'successfully created version: {versionName}')
    full_version_dict[versionName]=result
    all_versions[versionName]=result['id']
    return result

def timecode_to_frames(timecode, fps=24):
    hh, mm, ss, ff = map(int, timecode.split(':'))
    total_frames = (hh * 3600 + mm * 60 + ss) * fps + ff
    
    return total_frames


def gather_all_proxies(proxies_path):
    all_proxies = [y for x in os.walk(proxies_path) for y in glob(os.path.join(x[0], '*mp4'))]
    return all_proxies

def gather_all_video_files(PATH,type=""):
    all_proxies = [y for x in os.walk(PATH) for y in glob(os.path.join(x[0], f'*{type}'))]
    return all_proxies

def check_first_frame(version):
    version_name=version['code']
    version_id=version['id']
    if 'comp' not in version_name:
        first_frame=version['sg_first_frame']
        if first_frame==1001:
            timecode=proxy_timecode_dict[version_name]
            frame_num=timecode_to_frames(timecode)
            data={'sg_first_frame':frame_num}
            print(f'updating first frame for {version_name}')
            sg.update('Version',version_id,data)



def upload_to_SG(proxy,playlist_id):
    version_name=os.path.basename(proxy).split('.')[0]
    print(version_name)
    if "_sh0" not in version_name.lower() or "_sh1" not in version_name.lower():
        start_timecode=get_start_timecode(proxy)
        proxy_timecode_dict[version_name]=start_timecode
    else:
        start_timecode=""
    if version_name not in all_versions.keys():
        if "_sh0" in version_name.lower() or "_sh1" in version_name.lower():
            SeqCode,ShotCode=Quick_ParseCode(version_name)
            print(version_name,SeqCode)
            print('station 2')
            # time.sleep(5)
        else:
            SeqCode="zRAW_SHOTS"
            ShotCode=version_name

        if SeqCode not in all_sequences.keys():
            print(SeqCode)
            print('station 3')
            sequence_info=create_sequence(SeqCode)
            Sequence_ID=sequence_info['id']
        else:
            Sequence_ID=all_sequences[SeqCode]

        if ShotCode not in all_shots.keys():
            shot_info=create_shot(ShotCode,start_timecode,SeqCode,Sequence_ID)
            Shot_ID=shot_info['id']
        else:
            Shot_ID=all_shots[ShotCode]
        
        version_info=CreateVersion(version_name,start_timecode,playlist_id,proxy,Shot_ID)
        version_ID=version_info['id']

        try:
            sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
            sg.upload("Version", version_ID, proxy, field_name='sg_uploaded_movie',display_name=version_name)
            print(f'successfully uploaded {version_name}')
        except:
            try:
                sg = shotgun_api3.Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)
                sg.upload("Version", version_ID, proxy, field_name='sg_uploaded_movie',display_name=version_name)
                print(f'successfully uploaded {version_name}')
            except:
                variables_for_item=["Version", version_ID, proxy]
                didnt_make_it.append(variables_for_item)





global all_sequences 
all_sequences=Shotgun_Find_All_Sequences()
print(all_sequences)

global all_shots
all_shots=Shotgun_Find_All_Shots()

global all_versions
all_versions = Shotgun_Find_All_Versions()

global playlist_name
all_playlists=Shotgun_Find_All_Playlists()

global playlist_id



for i in range(1, len(sys.argv)):  # Skip the first argument, which is the script name
    if sys.argv[i] == "--playlist":
        playlist_name = sys.argv[i + 1]
    elif sys.argv[i] == "--target":
        target_folder = sys.argv[i + 1]
    elif sys.argv[i] == "--proxies":
        playlist_name = 'proxies'


try:
    if playlist_name not in all_playlists.keys():
        playlist_info=Create_Playlist(playlist_name)
        # global playlist_id
        playlist_id = playlist_info[0]['id']
    else:
        # global playlist_id
        playlist_id = all_playlists[playlist_name]
except:
    sys.exit('Need to enter playlist name as argument')
    

if '--delivery' in sys.argv:
    sys.argv.append('--review')

if '--review' in sys.argv:
    target_folder_1='/Volumes/Branching Out EDIT/Branching Out/VFX/Deliveries/MediaTeam/_INSERT_WORK_HERE'
    current_date = datetime.now()
    formatted_date = current_date.strftime('%Y%m%d')

    target_folder=f'/Volumes/Branching Out EDIT/Branching Out/VFX/Deliveries/MediaTeam/{formatted_date}'
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    all_files=gather_all_video_files(target_folder_1)
    for file in all_files:
        basename=os.path.basename(file)
        new_file=os.path.join(target_folder,basename)
        shutil.move(file,new_file)
    leftover_image_files=[]
    all_shots_path=target_folder
    all_image_files_1=gather_all_video_files(all_shots_path,'.png')
    all_image_files_2=gather_all_video_files(all_shots_path,'.jpg')
    all_image_files_3=gather_all_video_files(all_shots_path,'.exr')
    all_image_files_4=gather_all_video_files(all_shots_path,'.tiff')

    all_image_files=all_image_files_1+all_image_files_2+all_image_files_3+all_image_files_4
    for image_file in all_image_files:
        create_movie_from_still(image_file)

    all_video_files_1=gather_all_video_files(all_shots_path,'.mov')
    all_video_files_2=gather_all_video_files(all_shots_path,'.mp4')
    all_video_files=all_video_files_1+all_video_files_2+leftover_image_files

    for file in all_video_files:
        if 'exports' not in file.lower():
            file_base=os.path.basename(file)
            if '_source' not in file_base.lower() and 'reference.mp4' not in file_base.lower():
                print(file_base)
                upload_to_SG(file,playlist_id)

elif '--proxies' in sys.argv:
    proxies_path=r'/Volumes/Branching Out EDIT/Branching Out/Branching Out DRIVE DELIVERIES'
    all_proxies=gather_all_proxies(proxies_path)
    for proxy in all_proxies:
        if 'proxies' in proxy.lower():
            upload_to_SG(proxy,playlist_id)

elif '--new_sequence' in sys.argv:
    all_video_files=gather_all_video_files(target_folder,'.mp4')
    for file in all_video_files:
        if 'exports' not in file.lower():
            file_base=os.path.basename(file)
            if '_source' not in file_base.lower() and 'reference.mp4' not in file_base.lower():
                upload_to_SG(file,playlist_id)

else:
    sys.exit('must choose argument --new_sequence, --proxies, or --review')
    



