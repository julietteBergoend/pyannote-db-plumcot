echo PWD: ${PWD}
VIDEOS_PATH='/vol/work3/maurice/dvd_extracted'
SERIE_URI='Friends'
export DATA_PATH=/vol/work/lerner/pyannote-db-plumcot
export SERIE_PATH=${DATA_PATH}/Plumcot/data/${SERIE_URI}
#SEASON_NUMBER=01
SEASON_NUMBER=$1
export MODEL_NAME=dlib_face_recognition_resnet_model_v1
export DLIB_MODELS=/people/lerner/pyannote/pyannote-video/dlib-models
export DLIB_EMBEDDING=${DLIB_MODELS}/${MODEL_NAME}.dat
export DLIB_LANDMARKS=${DLIB_MODELS}/shape_predictor_68_face_landmarks.dat
echo MODEL_NAME: ${MODEL_NAME}
echo DLIB_MODELS: ${DLIB_MODELS}
echo DLIB_EMBEDDING: ${DLIB_EMBEDDING}
echo DLIB_LANDMARKS: ${DLIB_LANDMARKS}
for video_path in ${VIDEOS_PATH}/${SERIE_URI}/${SERIE_URI}.Season${SEASON_NUMBER}*.mkv; do
  file_name=`basename "${video_path}"`
  extension="${file_name##*.}"
  file_uri="${file_name%.*}"
  shots_path=${SERIE_PATH}/video/${file_uri}.shots.json
  features_path=${SERIE_PATH}/video/${file_uri}.npy
  echo video_path: ${video_path}
  echo shots_path: ${shots_path}
  echo features_path: ${features_path}
  # pyannote-structure.py shot --verbose ${video_path} \
  #                                      ${shots_path}
  # pyannote-face.py track --verbose --every=0.0 ${video_path} \
  #                                              ${shots_path} \
  #                                              ${features_path}
  pyannote-face.py extract --verbose ${video_path} \
                                     ${features_path} \
                                     ${DLIB_LANDMARKS} \
                                     ${DLIB_EMBEDDING} \
                                     ${features_path}
  pyannote-face.py identify --data_path=${DATA_PATH} --credits=${SERIE_PATH}/credits.txt --characters=${SERIE_PATH}/characters.txt --file_uri=${file_uri} ${SERIE_PATH}/images/images.json \
                                                                                                                                                          ${features_path} \
                                                                                                                                                          ${features_path}

done
