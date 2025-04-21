#!/bin/bash

imgName="ceph-api-backend"
targetPort=3001
externalPort=3001
lastTag=$(docker images | grep $imgName | awk '{print $2}')
if [ -z "$lastTag" ]; then
        lastTag="0.0.0"
fi

echo "*******************************************************"
echo "*******************************************************"
echo "*******************************************************"
echo "********* CEPH-API-BackEnd Build & run Script ********"
echo "*******************************************************"
echo "************* Last Image Version: $lastTag ***************"
echo "*******************************************************"

read -p 'Please enter the image tags: ' imgTag

if [ -z "$imgTag" ]; then
        echo "Not enter the tag! try agin"
        exit 1
elif [ "$lastTag" = "0.0.0" ]; then
	echo "Keep going img build & run"
elif [ "$imgTag" = "$lastTag" ]; then
        echo "I will keep the tag the same. The existing image will be deleted, and a new build will be executed."
	nowContainerRunning=$(docker ps -a | grep $imgName)
	if [ -n "$nowContainerRunning" ]; then
		docker stop $imgName
	fi
        
	docker rmi $imgName:$lastTag
elif [ "$imgTag" != "$lastTag" ]; then
        read -p "Should we keep the existing image?(Y/N): " keepingFlag
	keepingFlag=$(echo "$keepingFlag" | tr '[:upper:]' '[:lower:]') 
        if [ "$keepingFlag" = "y" ]; then
                #passing
                echo "keeping the existing image."
        elif [ "$keepingFlag" = "n" ]; then
                isItRunning=$(docker ps -a | grep $imgName | awk '{print $1}')
                if [ -z "$isItRunning" ]; then
                        #docker stop $(docker ps -a | grep "ceph-api-back" | awk '{print $1}'
                        #passing
                        echo "No running containers! Proceeding with image deletion."
                else
                        #docker stop $(docker ps -a | grep $imgName | awk '{print $1}')
			docker stop $imgName
                fi
                docker rmi $imgName:$lastTag
		break
        else
                echo "try again"
                exit 1
        fi
else
        echo "error"
        exit 1
fi

docker build --no-cache -t $imgName:$imgTag -f Dockerfile .

docker run -it --rm -d -p $externalPort:$targetPort --env-file config.env --name $imgName $imgName:$imgTag
