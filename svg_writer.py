import io
from bs4 import BeautifulSoup
import json
import math

from parser_base import ParserBase
from sexpressions_parser import parse_sexpression
from sexpressions_writer import SexpressionWriter

pxToMM = 3.779528


# kicad_pcb
# version
# host
# general
# page
# title_block
# layers
# setup
# net
# net_class
# module
# dimension
# gr_line
# gr_arc
# gr_text
# segment
# via
# zone

class FlexParse(object):
    def __init__(self):
        self.filename_in = "example/simple2.kicad_pcb"
        self.filename_json = "example/out.json"
        self.filename_svg = "example/out.svg"
        self.filename_base = "example/base.svg"


    def Load(self):
        with io.open(self.filename_in, 'r', encoding='utf-8') as f:
            sexpression = parse_sexpression(f.read())
        return sexpression

    def Convert(self, obj):
        js = json.dumps(obj)
        return js

    def Save(self, xml):
        with open(self.filename_json, 'w') as f:
            f.write(xml)

    def Print_Headings(self, dic):
        for item in dic:
            if type(item) is str:
                print(item)
            else:
                print(item[0])

    def Handle_Headings(self, items, base):
        # svg = ''
        dic = []
        segments = []
        if items[0] != 'kicad_pcb':
            assert False,"kicad_pcb: Not a kicad_pcb"

        base.svg.append(BeautifulSoup('<kicad />', 'html.parser'))
        base.svg.append(BeautifulSoup('<g inkscape:label="Vias" inkscape:groupmode="layer" id="layervia" user="True" />', 'html.parser'))
        
        i = 0
        for item in items:
            if type(item) is str:
                print(item)
            else:
                if item[0] == 'layers':
                    layers = self.Convert_Layers_To_SVG(item)
                   
                    for layer in layers:
                        tag = BeautifulSoup(layer, 'html.parser')
                        base.svg.append(tag)

                elif item[0] == 'segment':
                    tag = BeautifulSoup(self.Convert_Segment_To_SVG(item, i), 'html.parser')
                    layer = tag.path['layer']
                    base.svg.find('g', {'inkscape:label': layer}, recursive=False).append(tag)

                elif item[0] == 'module':
                    base.svg.append(self.Convert_Module_To_SVG(item, i))

                elif item[0] == 'gr_line':
                    tag = BeautifulSoup(self.Convert_Gr_Line_To_SVG(item, i), 'html.parser')
                    layer = tag.path['layer']
                    base.svg.find('g', {'inkscape:label': layer}, recursive=False).append(tag)

                elif item[0] == 'gr_arc':
                    tag = BeautifulSoup(self.Convert_Gr_Arc_To_SVG(item, i), 'html.parser')
                    layer = tag.path['layer']
                    base.svg.find('g', {'inkscape:label': layer}, recursive=False).append(tag)

                elif item[0] == 'via':
                    tag = BeautifulSoup(self.Convert_Via_To_SVG(item, i), 'html.parser')
                    base.svg.find('g', {'inkscape:label': 'Vias'}, recursive=False).append(tag)
                else:
                    # print(item[0])
                    svg = self.Convert_Metadata_To_SVG(item)
                    base.svg.kicad.append(BeautifulSoup(svg, 'html.parser'))
            i = i + 1
        dic.append({'segment': segments})

        svg = base.prettify("utf-8")
        with open(self.filename_svg, "wb") as file:
            file.write(svg)

        return dic



    def Convert_Metadata_To_SVG(self, input):
        # This will just take whatever data and store it in an XML tag as JSON
        # Hacky, but we don't care about it other than to be able to load it back in later

       
        tag = input[0]
        #input = input[1:]
        
        body = json.dumps(input)
        
        svg = '<' + tag + '>'
        svg += body
        svg += '</' + tag + '>'

        return body + ','

    def Convert_Layers_To_SVG(self, input):
        # 0 layers
        # 1
        #   0 1-whatever layerid
        #   1 F.Cu
        #   2/3 user/hide(optional)
        # 2 ...
        # 3 ...

        i = 0
        layers = []
    
        if input[0] != 'layers':
            assert False,"Layers: Not a layer"
            return None

        for item in input:
            i = i + 1
            if i == 1:
                continue

            layerid = item[0]
            layername = item[1]

            user = ''
            hide = ''
            signal = ''
            power = ''
            if 'user' in item:
                user = 'user="True" '
            if 'hide' in item:
                hide = 'hide="True" '
            if 'signal' in item:
                signal = 'signal="True" '
            if 'power' in item:
                power = 'power="True" '


            parameters = '<g '
            parameters += 'inkscape:label="' + layername + '" '
            parameters += 'inkscape:groupmode="layer" '
            parameters += 'id="layer' + layerid + '"'
            parameters += 'number="' + layerid + '"'
            parameters += user
            parameters += hide
            parameters += signal
            parameters += power
            parameters += '/>'

            layers.append(parameters)
            i = i + 1
        
        # return {'layers': layers }
        return layers

    def Convert_Segment_To_SVG(self, input, id):
        # 0 segment
        # 1
        #   0 start
        #   1 66.66
        #   2 99.99
        # 2
        #   0 end
        #   1 66.66
        #   2 99.99
        # 3
        #   0 width
        #   1 0.25
        # 4
        #   0 layer
        #   1 B.Cu
        # 5
        #   0 net
        #   1 1

        start = []
        end = []

        if input[0] != 'segment':
            assert False,"Segment: Not a segment"
            return None

        if input[1][0] != 'start':
            assert False,"Segment: Start out of order"
            return None

        start.append(input[1][1])
        start.append(input[1][2])

        if input[2][0] != 'end':
            assert False,"Segment: End out of order"
            return None

        end.append(input[2][1])
        end.append(input[2][2])

        if input[3][0] != 'width':
            assert False,"Segment: Width out of order"
            return None

        width = input[3][1]

        if input[4][0] != 'layer':
            assert False,"Segment: Layer out of order"
            return None

        layer = input[4][1]

        if input[5][0] != 'net':
            assert False,"Segment: Net out of order"
            return None

        net = input[5][1]

        parameters = '<path style="fill:none;stroke-linecap:round;stroke-linejoin:miter;stroke-opacity:1'
        parameters += ';stroke:#' + self.Assign_Layer_Colour(layer)
        parameters += ';stroke-width:' + width + 'mm'
        parameters += '" '
        parameters += 'd="M ' + str(float(start[0]) * pxToMM) + ',' + str(float(start[1]) * pxToMM) + ' ' + str(float(end[0]) * pxToMM) + ',' + str(float(end[1]) * pxToMM) + '" '
        # parameters += 'd="M ' + start[0] + ',' + start[1] + ' ' + end[0] + ',' + end[1] + '" '
        parameters += 'id="path' + str(id) + '" '
        parameters += 'layer="' + layer + '" '
        parameters += 'type="segment" '
        parameters += 'net="' + net + '" '
        parameters += '/>'

        # print(parameters)
        return parameters

    def Convert_Module_To_SVG(self, input, id):
        # 0 module
        # 1 Diode_SMD:D_SMD_SOD123
        # 2
        #   0 layer
        #   1 B.Cu
        # 3
        #   0 tstamp
        #   1 0DF
        # 4
        #   0 at
        #   1 66.66
        #   2 99.99
        # 3
        #   0 descr
        #   1 0.25
        # 4
        #   0 tags
        #   1 B.Cu
        # 5
        #   0 path
        #   1 1
        # 5
        #   0 attr
        #   1 1
        # 5
        #   0 fp_text / fp_line / fp_text / pad
        #   1 1
        #....
        #....

        at = []
        # svg = BeautifulSoup('<g inkscape:groupmode="layer" type="module" inkscape:label="module' + str(id) + '" id="module' + str(id) + '">', 'html.parser')
        svg = BeautifulSoup('<g type="module" inkscape:label="module' + str(id) + '" id="module' + str(id) + '" name="' + input[1] + '">', 'html.parser')
        
        if input[0] != 'module':
            assert False,"Module: Not a module"
            return None

        a = 0

        for item in input:


            if item[0] == 'at':

                at.append(item[1])
                at.append(item[2])
                transform = 'translate(' + str(float(item[1]) * pxToMM) + ',' + str(float(item[2]) * pxToMM) + ')'

                if len(item) > 3:
                    rotate = str(-1 * float(item[3]))
                    transform += ' rotate(' + rotate + ')'

                svg.g['transform'] = transform

            if item[0] == 'layer':

                svg.g['layer'] = item[1]

            if item[0] == 'fp_line':
                tag = BeautifulSoup(self.Convert_Gr_Line_To_SVG(item, str(id) + '-' + str(a)), 'html.parser')
                svg.g.append(tag)
            elif item[0] == 'pad':
                tag = BeautifulSoup(self.Convert_Pad_To_SVG(item, str(id) + '-' + str(a)), 'html.parser')
                svg.g.append(tag)

            a += 1

        return svg

    def Convert_Gr_Arc_To_SVG(self, input, id):
        # 0 gr_arc
        # 1
        #   0 start
        #   1 66.66
        #   2 99.99
        # 2
        #   0 end
        #   1 66.66
        #   2 99.99
        # 3
        #   0 angle
        #   1 -90
        # 4
        #   0 layer
        #   1 Edge.Cuts
        # 5
        #   0 width
        #   1 0.05
        # 6
        #   0 tstamp
        #   1 5E451B20

        start = []
        end = []
        centre = []

        if input[0] != 'gr_arc' and input[0] != 'fp_arc':
            assert False,"Gr_arc: Not a gr_arc"
            return None

        if input[1][0] != 'start':
            assert False,"Gr_arc: Start out of order"
            return None

        centre.append(float(input[1][1]) * pxToMM)
        centre.append(float(input[1][2]) * pxToMM)

        if input[2][0] != 'end':
            assert False,"Gr_arc: End out of order"
            return None

        start.append(float(input[2][1]) * pxToMM)
        start.append(float(input[2][2]) * pxToMM)

        if input[3][0] != 'angle':
            assert False,"Gr_arc: Angle out of order"
            return None

        angle = float(input[3][1])

        if input[4][0] != 'layer':
            assert False,"Gr_arc: Layer out of order"
            return None

        layer = input[4][1]

        if input[5][0] != 'width':
            assert False,"Gr_arc: Width out of order"
            return None

        width = input[5][1]

        tstamp = ''
        if(len(input) > 6):
            if input[6][0] != 'tstamp':
                assert False,"Gr_arc: tstamp out of order"
                return None

            tstamp = 'tstamp="' + input[6][1] + '" '

        # m 486.60713,151.00183 a 9.5535717,9.5535717 0 0 1 -9.55357,9.55357
        # (rx ry x-axis-rotation large-arc-flag sweep-flag x y)

        dx = start[0] - centre[0]
        dy = centre[1] - start[1]
        r = math.hypot(dx, dy)

        print(dx, dy, r, angle)

        angle = math.radians(angle)

        # startangle = (math.pi / 2) - math.asin(dx / r)
        startangle =  math.asin(dy / r)
        endangle = startangle - angle

        print(math.degrees(startangle))
        print(math.degrees(endangle))

        end.append((math.cos(endangle) * r) - dx)
        end.append(dy - (math.sin(endangle) * r))
        print([dx, dy])
        print([(math.cos(endangle) * r), (math.sin(endangle) * r)])
        print(end)

        r = str(r)

        print('')
        print('')
        print('')
        
        sweep = str(int(((angle / abs(angle)) + 1) / 2))
        if angle > 180:
            large = '1'
        else:
            large = '0'
        a = ' '.join(['a', r + ',' + r, '0', large, sweep, str(end[0]) + ',' + str(end[1])])

        parameters = '<path style="fill:none;stroke-linecap:round;stroke-linejoin:miter;stroke-opacity:1'
        parameters += ';stroke:#' + self.Assign_Layer_Colour(layer)
        parameters += ';stroke-width:' + width + 'mm'
        parameters += '" '
        parameters += 'd="M ' + str(start[0]) + ',' + str(start[1]) + ' ' + a + '" '
        parameters += 'id="path' + str(id) + '" '
        parameters += 'layer="' + layer + '" '
        parameters += 'type="gr_arc" '
        parameters += tstamp
        parameters += '/>'

        return parameters

    def Convert_Gr_Line_To_SVG(self, input, id):
        # 0 gr_line
        # 1
        #   0 start
        #   1 66.66
        #   2 99.99
        # 2
        #   0 end
        #   1 66.66
        #   2 99.99
        # 3
        #   0 layer
        #   1 Edge.Cuts
        # 4
        #   0 width
        #   1 0.05
        # 5
        #   0 tstamp
        #   1 5E451B20

        start = []
        end = []

        if input[0] != 'gr_line' and input[0] != 'fp_line':
            assert False,"Gr_line: Not a gr_line"
            return None

        if input[1][0] != 'start':
            assert False,"Gr_line: Start out of order"
            return None

        start.append(input[1][1])
        start.append(input[1][2])

        if input[2][0] != 'end':
            assert False,"Gr_line: End out of order"
            return None

        end.append(input[2][1])
        end.append(input[2][2])

        if input[3][0] != 'layer':
            assert False,"Gr_line: Layer out of order"
            return None

        layer = input[3][1]

        if input[4][0] != 'width':
            assert False,"Gr_line: Width out of order"
            return None

        width = input[4][1]

        tstamp = ''
        if(len(input) > 5):
            if input[5][0] != 'tstamp':
                assert False,"Gr_line: tstamp out of order"
                return None

            tstamp = 'tstamp="' + input[5][1] + '" '

        parameters = '<path style="fill:none;stroke-linecap:round;stroke-linejoin:miter;stroke-opacity:1'
        parameters += ';stroke:#' + self.Assign_Layer_Colour(layer)
        parameters += ';stroke-width:' + width + 'mm'
        parameters += '" '
        parameters += 'd="M ' + str(float(start[0]) * pxToMM) + ',' + str(float(start[1]) * pxToMM) + ' ' + str(float(end[0]) * pxToMM) + ',' + str(float(end[1]) * pxToMM) + '" '
        parameters += 'id="path' + str(id) + '" '
        parameters += 'layer="' + layer + '" '
        parameters += 'type="gr_line" '
        parameters += tstamp
        parameters += '/>'

        return parameters

    def Convert_Via_To_SVG(self, input, id):
        # 0 via
        # 1
        #   0 at
        #   1 66.66
        #   2 99.99
        # 2
        #   0 size
        #   1 0.6
        # 3
        #   0 drill
        #   1 0.3
        # 4
        #   0 layers
        #   1 F.Cu
        #   2 B.Cu
        # 5
        #   0 net
        #   1 16

        at = []
        layers = []

        if input[0] != 'via':
            assert False,"Via: Not a via"
            return None

        if input[1][0] != 'at':
            assert False,"Via: At out of order"
            return None

        at.append(input[1][1])
        at.append(input[1][2])

        if input[2][0] != 'size':
            assert False,"Via: Size out of order"
            return None

        size = input[2][1]

        if input[3][0] != 'drill':
            assert False,"Via: Layer out of order"
            return None

        drill = input[3][1]

        if input[4][0] != 'layers':
            assert False,"Via: Layers out of order"
            return None

        layers.append(input[4][1])
        layers.append(input[4][2])

        if input[5][0] != 'net':
            assert False,"Via: Net out of order"
            return None

        net = input[5][1]

        status = ''
        tstamp = ''
        if len(input) > 6:
            if input[6][0] == 'tstamp':
                tstamp = 'tstamp="' + input[6][1] + '" '
            elif input[6][0] == 'status':
                status = 'status="' + input[6][1] + '" '
            
        if len(input) > 7:
            if input[7][0] == 'tstamp':
                tstamp = 'tstamp="' + input[7][1] + '" '
            elif input[7][0] == 'status':
                status = 'status="' + input[7][1] + '" '


        parameters = '<circle style="stroke:none;stroke-linecap:round;stroke-linejoin:miter;fill-opacity:1'
        parameters += ';fill:#' + self.Assign_Layer_Colour('Edge.Cuts')
        parameters += '" '
        parameters += 'cx="' + str(float(at[0]) * pxToMM) + '" '
        parameters += 'cy="' + str(float(at[1]) * pxToMM) + '" '
        parameters += 'id="path' + str(id) + '" '
        parameters += 'r="' + str(float(size)  * (pxToMM / 2)) + '" '
        parameters += 'layers="' + layers[0] + ',' + layers[1] + '" '
        parameters += 'size="' + size + '" '
        parameters += 'drill="' + drill + '" '
        parameters += 'net="' + net + '" '
        parameters += tstamp
        parameters += status
        parameters += '/>'

        #print(parameters)
        return parameters

    def Convert_Pad_To_SVG(self, input, id):
        # 0 pad
        # 1 1/2/3
        # 2 smd
        # 3 rect
        # 4
        #   0 at
        #   1 66.66
        #   2 99.99
        #   2 180
        # 5
        #   0 size
        #   1 0.9
        #   2 1.2
        # 6
        #   0 layers
        #   1 F.Cu
        #   2 F.Paste
        #   3 F.Mask
        # 7
        #   0 net
        #   1 16
        #   2 Net-(D4-Pad1)

        at = []
        size = []
        layers = []
        roundrect_rratio = ''
        net = ''
        rotate = ''

        if input[0] != 'pad':
            assert False,"Pad: Not a pad"
            return None

        pin = input[1]

        process = input[2]

        for row in input:
            if len(row) > 1:
                if row[0] == 'at':
                    at.append(float(row[1]))
                    at.append(float(row[2]))

                    if len(row) > 3:
                        rotate = 'rotate="' + row[3] + '"'

                if row[0] == 'size':
                    size.append(row[1])
                    size.append(row[2])

                if row[0] == 'roundrect_rratio':
                    ratio = row[1]
                    roundrect_rratio = 'roundrect_rratio="' + row[1] + '"'

                if row[0] == 'net':
                    net = 'net="' + row[1] + '" '
                    net += 'netname="' + row[2] + '"'

                if row[0] == 'layers':
                    row = row[1:]

                    for layer in row:
                        layers.append(layer)


        shape = input[3]

        svg = ''
        svgsize = ''
        roundcorners = ''
        first = True

        for layer in layers:
            parameters = ''
            if shape == 'rect':

                # Corner coordinates to centre coordinate system
                x = at[0] - float(size[0]) / 2
                y = at[1] - float(size[1]) / 2

                parameters += '<rect style="stroke:none;stroke-linecap:round;stroke-linejoin:miter;fill-opacity:1'
                svgsize += 'x="' + str(x * pxToMM) + '" '
                svgsize += 'y="' + str(y * pxToMM) + '" '
                svgsize += 'width="' + str(float(size[0])  * pxToMM) + '" '
                svgsize += 'height="' + str(float(size[1])  * pxToMM) + '" '
            elif shape == 'roundrect':
                
                # Corner coordinates to centre coordinate system
                x = at[0] - float(size[0]) / 2
                y = at[1] - float(size[1]) / 2

                parameters += '<rect style="stroke:none;stroke-linecap:round;stroke-linejoin:miter;fill-opacity:1'
                roundcorners += 'rx="' + str(float(size[0]) * float(ratio)  * pxToMM) + '" '
                roundcorners += 'ry="' + str(float(size[1]) * float(ratio)  * pxToMM) + '" '
                svgsize += 'x="' + str(x * pxToMM) + '" '
                svgsize += 'y="' + str(y * pxToMM) + '" '
                svgsize += 'width="' + str(float(size[0])  * pxToMM) + '" '
                svgsize += 'height="' + str(float(size[1])  * pxToMM) + '" '
            elif shape == 'circle':
                parameters += '<circle style="stroke:none;stroke-linecap:round;stroke-linejoin:miter;fill-opacity:1'
                svgsize += 'cx="' + str(at[0] * pxToMM) + '" '
                svgsize += 'cy="' + str(at[1] * pxToMM) + '" '
                svgsize += 'r="' + str(float(size[0])  * (pxToMM / 2)) + '" '
                svgsize += 'height="' + str(float(size[1])  * pxToMM) + '" '
            elif shape == 'oval':
                parameters += '<circle style="stroke:none;stroke-linecap:round;stroke-linejoin:miter;fill-opacity:1'
                svgsize += 'cx="' + str(at[0] * pxToMM) + '" '
                svgsize += 'cy="' + str(at[1] * pxToMM) + '" '
                svgsize += 'r="' + str(float(size[0])  * (pxToMM / 2)) + '" '
                svgsize += 'height="' + str(float(size[1])  * pxToMM) + '" '
            else:
                assert False,"Pad: Unfamiliar shape: " + shape
                return None

            parameters += ';fill:#' + self.Assign_Layer_Colour(layer)
            parameters += '" '
            parameters += 'id="path-' + str(id) + '-' + layer + '" '
            parameters += svgsize
            parameters += roundcorners
            parameters += roundrect_rratio
            parameters += net
            parameters += rotate
            parameters += 'process="' + process + '"'
            parameters += 'pin="' + pin + '"'
            if first == True:
                parameters += 'first="True"'
                parameters += 'layers="' + ','.join(layers) + '"'
            parameters += '/>'

            svg += parameters
            first = False

        #print(parameters)
        return svg

    def Assign_Layer_Colour(self, layername):
        colours = {
            'F.Cu': '840000',
            'In1.Cu': 'C2C200',
            'In2.Cu': 'C200C2',
            'B.Cu': '008400',
            'B.Adhes': '840084',
            'F.Adhes': '000084',
            'B.Paste': '000084',
            'F.Paste': '840000',
            'B.SilkS': '840084',
            'F.SilkS': '008484',
            'B.Mask': '848400',
            'F.Mask': '840084',
            'Dwgs.User': 'c2c2c2',
            'Cmts.User': '000084',
            'Eco1.User': '008400',
            'Eco2.User': 'c2c200',
            'Edge.Cuts': 'C2C200',
            'Margin': 'c200c2',
            'B.CrtYd': '848484',
            'F.CrtYd': 'c2c2c2',
            'B.Fab': '000084',
            'F.Fab': '848484',
            'Default': 'FFFF00'
        }

        if layername in colours:
            return colours[layername]
        else:
            return colours['Default']
        
        


    def Run(self):
        dic = self.Load()
        # self.Print_Headings(dic)
        #js = self.Convert(dic)
        #self.Save(js)
        
        with open(self.filename_base, "r") as f:
    
            contents = f.read()
            base = BeautifulSoup(contents, 'html.parser')
        

        tags = self.Handle_Headings(dic, base)

        # writer = SvgWriter(tags)

        # writer.Display()


if __name__ == '__main__':
    e = FlexParse()
    e.Run()