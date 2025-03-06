#!/bin/bash

echo "*******************************************************"
echo "*******************************************************"
echo "*******************************************************"
echo "********* CEPH-API-Backend Build & run Script *********"
echo "*******************************************************"
echo "*******************************************************"
echo "*******************************************************"

imgName="ceph-api-back"
targetPort=5000
externalPort=5000
lastTag=$(docker images | grep ceph-api-back | awk '{print $2}')

read -p 'Please enter the image tags: ' imgTag

if [ -z "$imgTag" ]; then
	echo "Not enter the tag! try agin"
elif [ "$imgTag" = "$lastTag" ]; then
	echo "I will keep the tag the same. The existing image will be deleted, and a new build will be executed."
	docker rmi $imgName:$lastTag
	docker build -t $imgName:$imgTag -f Dockerfile .
elif [ "$imgTag" != "$lastTag" ]; then
	read -p "Should we keep the existing image?(Y/N): " keepingFlag
	if [ "$keepingFlag" = "Y" ]; then
		#passing
		echo "keeping the existing image."
	elif [ "$keepingFlag" = "N" ]; then
		isItRunning=$(docker ps -a | grep $imgName | awk '{print $1}')
		if [ -z "$isItRunning" ]; then
			#docker stop $(docker ps -a | grep "ceph-api-back" | awk '{print $1}'
			#passing
			echo "No running containers! Proceeding with image deletion."
		else
			docker stop $(docker ps -a | grep $imgName | awk '{print $1}')
		fi
		docker rmi $imgName:$lastTag
	else
		echo "try again"
		exit 1
	fi
	docker build -t $imgName:$imgTag -f Dockerfile .
else
	echo "error"
	exit 1
fi

docker run -it --rm -p $externalPort:$targetPort --env-file config.env $imgName:$imgTag


#docker build -t ceph-api-back:$ -f Dockerfile .
#docker run -it --rm -p 5000:5000 --env-file config.env ceph-api-back:$img
