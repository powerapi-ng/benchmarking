echo "Transforming alumet files"
./transform_alumet.sh $1

echo "Transforming codecarbon files"
./transform_codecarbon.sh $1

echo "Transforming scaphandre files"
./transform_scaphandre.sh $1

echo "Transforming vjoule files"
./transform_vjoule.sh $1
