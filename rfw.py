import subprocess, json, configparser, netaddr
from collections import OrderedDict
from flask import Flask, request, abort
from flask_basicauth import BasicAuth


app = Flask(__name__)

config = configparser.ConfigParser()
config.read('auth.conf')
app.config['BASIC_AUTH_USERNAME'] = config['auth']['username']
app.config['BASIC_AUTH_PASSWORD'] = config['auth']['password']
basic_auth = BasicAuth(app)


APP_URL = "http://localhost:5000"

white_list = []
ipconf = configparser.ConfigParser(allow_no_value=True)
ipconf.read('white.list')
for nwks in ipconf['auth_ip']:#read ip networks
	white_list.extend([str(ip) for ip in netaddr.IPNetwork(nwks)])#make a list of all the ip addresses in the network 


@app.route('/list', methods = ['GET'])
@basic_auth.required #requires valid username and password
def list_rules():# listing rules
	if request.method == 'GET':
		table = request.args.to_dict().setdefault('table', 'filter')#list filter table rules by default
		return subprocess.check_output(['iptables', '-t', table, '-L'])


valid_options = set(['table', 'chain', 'protocol', 'src', 'dst', 'in_iface', 'out_iface', 'dport', 'target', 'to_destination'])
@app.route('/', methods = ['POST', 'DELETE'])
@basic_auth.required
def modify_rules():
	cmd = OrderedDict()
	data = request.get_json(force=True)
	if not set(data.keys()).issubset(valid_options):#check if the arguments in json are valid
		invalid_args = set(data.keys()) - valid_options
		return "'" + invalid_args.pop() + "'" + "is an invalid option"

	cmd['-t'] = data.setdefault('table', 'filter')#use filter table if not specified
	cmd['-p'] = data.setdefault('protocol', '')#empty strings in value if argument not provided
	cmd['-s'] = data.setdefault('src', '')
	cmd['-d'] = data.setdefault('dst', '')
	cmd['-i'] = data.setdefault('in_iface', '')
	cmd['-o'] = data.setdefault('out_iface', '')
	cmd['--dport'] = data.setdefault('dport', '')
	cmd['-j'] = data.setdefault('target', '').upper()	
	cmd['--to'] = data.setdefault('to_destination', '')
	

	if 'chain' not in data.keys():#checking mandatory arguments
		return "Chain required"

	if data['target'].upper() == 'MASQUERADE' or data['target'].upper() == 'SNAT':#checking for invalid target-chain combination 
		if data['chain'].upper() != 'POSTROUTING':
			return "Incorrect Chain"			
	if data['target'].upper() == 'DNAT':
		if data['chain'].upper() != 'PREROUTING':
			return "Incorrect Chain"
	if 'dport' in data.keys() and 'protocol' not in data.keys():
		return "'protocol' required"
	if request.method == 'POST':#use 
		cmd['-A'] = data.setdefault('chain').upper()
	if request.method == 'DELETE':
		cmd['-D'] = data.setdefault('chain').upper()

	cmdl = ['iptables']
	for opt, val in cmd.items():# making command in the form(['iptables', '-p', 'tcp'...])
		if val != '':#skipping arguments if not provided
			cmdl.append(opt)
			cmdl.append(val)
	try:
		print cmdl
		res = subprocess.check_output(cmdl)
		subprocess.check_output(['iptables-save'])#save if successfully executed	
	except subprocess.CalledProcessError as e:
		return "\nError Executing command\n" + str(e) + "\n"
	except Exception, e:
		return str(e)
	return res


@app.before_request #invokes before 
def limit_remote_addr():#allow only white listed IP addresses
    if request.remote_addr not in white_list:
        abort(401)




if __name__ == "__main__":
    app.run(host= '0.0.0.0', debug=True)
