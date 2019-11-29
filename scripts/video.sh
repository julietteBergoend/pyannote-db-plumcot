#!/bin/bash

#$ -N face-tracking
#$ -S /bin/bash
#$ -o /vol/work/lerner/logs/output/
#$ -e /vol/work/lerner/logs/error/
#$ -v LD_LIBRARY_PATH
#$ -v PATH

echo "This is task ${SGE_TASK_ID} of job ${JOB_ID}."
export ffmpeg=/people/bredin/cluster/bin/ffmpeg
export file_uri=`head -n ${SGE_TASK_ID} $1 | tail -n 1`
echo $file_uri
export MODEL_NAME=dlib_face_recognition_resnet_model_v1
export DLIB_MODELS=/people/lerner/pyannote/pyannote-video/dlib-models
export DLIB_EMBEDDING=${DLIB_MODELS}/${MODEL_NAME}.dat
export DLIB_LANDMARKS=${DLIB_MODELS}/shape_predictor_68_face_landmarks.dat
echo ${MODEL_NAME}
echo ${DLIB_MODELS}
echo ${DLIB_EMBEDDING}
echo ${DLIB_LANDMARKS}
export VIDEOS_PATH=/vol/work3/maurice/dvd_extracted
export DATA_PATH=/vol/work/lerner/pyannote-db-plumcot/Plumcot/data
export SERIE_URI=$2
export SERIE_PATH=${DATA_PATH}/${SERIE_URI}
export video_path=${VIDEOS_PATH}/${SERIE_URI}/$file_uri.mkv
export shots_path=${SERIE_PATH}/video/${file_uri}.shots.json
export features_path=${SERIE_PATH}/video/${file_uri}.npy
echo ${video_path}
echo ${shots_path}
echo ${features_path}
`which pyannote-structure.py` shot --verbose --ffmpeg=${ffmpeg} ${video_path} \
                                                                ${shots_path}
`which pyannote-face.py` track --verbose --every=0.0 --ffmpeg=${ffmpeg} ${video_path} \
                                                                        ${shots_path} \
                                                                        ${features_path}
`which pyannote-face.py` extract --verbose --ffmpeg=${ffmpeg} ${video_path} \
                                                              ${features_path} \
                                                              ${DLIB_LANDMARKS} \
                                                              ${DLIB_EMBEDDING} \
                                                              ${features_path}
