#!/bin/bash
# Start an experiment
source experimentconfig.sh

argos_configuration() {
<<<<<<< HEAD
    marker="/r/"
    grep -o -P '(?<=/r/).*(?=/r/)' $ARGOSTEMPLATE 
    grep -o -P '(?<=$marker).*(?=$marker)' $ARGOSTEMPLATE | while read -r match ; do
      echo $match
      if [[ ! -n "$match" ]]; then
          echo "Please add $match to experimentconfig.sh"
      fi
    done
   # sed -e "s|${marker}match${marker}|$match|g" $ARGOSTEMPLATE > $ARGOSFILE
=======
    start="/s/"
    end="/e/"
    grep -o -P "(?<=$start).*(?=$end)" $ARGOSTEMPLATE | while read -r match ; do
      echo $match
      if [[ ! -n $(echo $match) ]]; then
        echo "Please add $match to experimentconfig.sh"
      fi
    done
>>>>>>> bc61d6d3386d960c32a609a8fdd94847f72cf512

}

argos_configuration