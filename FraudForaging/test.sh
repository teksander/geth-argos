#!/bin/bash
# Start an experiment
source experimentconfig.sh

argos_configuration() {
    marker="/r/"
    grep -o -P '(?<=/r/).*(?=/r/)' $ARGOSTEMPLATE 
    grep -o -P '(?<=$marker).*(?=$marker)' $ARGOSTEMPLATE | while read -r match ; do
      echo $match
      if [[ ! -n "$match" ]]; then
          echo "Please add $match to experimentconfig.sh"
      fi
    done
   # sed -e "s|${marker}match${marker}|$match|g" $ARGOSTEMPLATE > $ARGOSFILE

}

argos_configuration