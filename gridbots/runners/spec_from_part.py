"""

"""

import os
import sys
from jinja2 import Template
import gridbots

SPEC_TEMPLATE = 'dual_build_part.yml.template'


def spec_from_part(part_file):

    script_path = os.path.dirname(os.path.realpath(__file__))
    spec_path = os.path.join(script_path, SPEC_TEMPLATE)

    with open(spec_path, 'r') as f:
        template = Template(f.read())

    s = template.render(part_file=part_file)

    output_path = os.path.join(gridbots.path, 'spec', 'simulations', 'dual_build_part.yml')
    with open(output_path, 'w') as f:
        f.write(s)

if __name__ == '__main__':

    spec_from_part(part_file=sys.argv[1])
