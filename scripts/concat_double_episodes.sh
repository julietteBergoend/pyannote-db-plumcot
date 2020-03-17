export SERIE_URI=$1
export WAV_PATH=$2
export EXTENSION=en16kHz.wav
for file in Plumcot/data/$SERIE_URI/double_episodes/*.txt; do
	echo file: $file
	file_name=`basename "${file}"`
	file_uri="${file_name%.*}"
	output=$WAV_PATH/$1/$file_uri.$EXTENSION
	echo output: $output
	ffmpeg -f concat -safe 0 -i $file -c copy $output
done
