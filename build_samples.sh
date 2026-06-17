#!/usr/bin/sh
cd output
echo "<html>" > index.html
echo "<body>" >> index.html

for i in `ls | awk 'BEGIN{FS="_";}{print $2}' | sort -un`; do 
  echo $i
  convert -background none -bordercolor none -gravity center \*_"$i"_\*_front_\* +append \*_"$i"_back_\* +append $i.jpg
  echo "<a href=\"$i.jpg\"><img style=\"width:100%\" src=\"$i.jpg\"></a><br><hr>" >> index.html
done

echo "</body>" >> index.html
echo "</html>" >> index.html
