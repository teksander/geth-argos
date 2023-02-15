#!/bin/bash
# Start an experiment
source experimentconfig.sh

argos_configuration() {
    start="/s/"
    end="/e/"
    grep -o -P "(?<=$start).*(?=$end)" $ARGOSTEMPLATE | while read -r match ; do
      echo $match
      if [[ ! -n $(echo $match) ]]; then
        echo "Please add $match to experimentconfig.sh"
      fi
    done

}

argos_configuration