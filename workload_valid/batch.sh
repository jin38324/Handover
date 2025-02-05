counter=0
while [ $counter -lt 10 ] 
do
	    python upload.py &
	    ((counter++)) 
    done
