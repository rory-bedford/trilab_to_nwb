import json

behave_json = {
    'specification': 'antelope-behaviour',
    'version': '0.0.1',
    'reference_point': 'center of scales',
    'features': [],
    'videos': []
}

video = {}
video['name'] = 'behaviour_video'
video['description'] = 'Top down video of the behaviour'
video['format'] = 'avi'
behave_json['videos'].append(video)

coords = [
        [1.366, 0.5, 0.0],
        [0.0, 1.0, 0.0],
        [-1.366, 0.5 ,0.0],
        [-1.366, -0.5, 0.0],
        [0.0, -1.0, 0.0],
        [1.366, -0.5, 0.0]
    ]

# add DLC features
for i in ['right_ear','spine_2','spine_1','nose','spine_3','spine_4','left_ear','head']:

    feature = {}
    feature['name'] = i
    feature['source'] = {'source_type': 'processing', 'module': 'behaviour_coords', 'video': 'behaviour_video'}
    feature['ownership'] = {'ownership': 'self', 'animal':1}
    feature['data_type'] = 'kinematics'
    feature['description'] = 'Externally processed DLC coordinates for ' + i
    behave_json['features'].append(feature)


for i in ['BUZZER','LED_','SPOT']:

    for j in range(1,7):

        feature = {}
        feature['name'] = i + str(j)
        feature['source'] = {'source_type': 'stimulus'}
        feature['ownership'] = {'ownership': 'world'}
        feature['data_type'] = 'interval'
        feature['coordinates'] = coords[j-1]
        feature['description'] = 'Intervals for ' + i + str(j)

        behave_json['features'].append(feature)

for j in range(1,7):

    feature = {}
    feature['name'] = 'VALVE' + str(j)
    feature['source'] = {'source_type': 'stimulus'}
    feature['ownership'] = {'ownership': 'world'}
    feature['data_type'] = 'digital'
    feature['coordinates'] = coords[j-1]
    feature['description'] = 'Condensed milk reward at port ' + str(j)

    behave_json['features'].append(feature)


for i in ['GO_CUE', 'NOGO_CUE']:

    feature = {}
    feature['name'] = i
    feature['source'] = {'source_type': 'stimulus'}
    feature['ownership'] = {'ownership': 'world'}
    feature['data_type'] = 'interval'
    feature['coordinates'] = [0.0, 0.0, 0.0]
    feature['description'] = 'Intervals for ' + i

    behave_json['features'].append(feature)

for i in ['SENSOR']:

    for j in range(1,7):

        feature = {}
        feature['name'] = i + str(j)
        feature['source'] = {'source_type': 'acquisition'}
        feature['ownership'] = {'ownership': 'world'}
        feature['data_type'] = 'interval'
        feature['coordinates'] = coords[j-1]
        feature['description'] = 'Intervals for SENSOR' + str(j)

        behave_json['features'].append(feature)

feature = {}
feature['name'] = 'scales'
feature['source'] = {'source_type': 'acquisition'}
feature['ownership'] = {'ownership': 'world'}
feature['data_type'] = 'analog'
feature['coordinates'] = [0.0, 0.0, 0.0]
feature['description'] = 'Scales data'

behave_json['features'].append(feature)

with open('stefan_rig.json','w') as f:
    json.dump(behave_json, f, indent=4)
