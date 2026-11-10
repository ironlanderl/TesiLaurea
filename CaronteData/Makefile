.PHONY: caronte-user25
caronte-user25:
	curl -X POST "http://127.0.0.1:3333/setup" -H "Content-Type: application/json" -d '{"config":{"server_address":"10.60.38.1","flag_regex":"[A-Z0-9]{31}=","auth_required":false},"accounts":{"a": "b"}}'

.PHONY: caronte-user26
caronte-user26:
	curl -X POST "http://127.0.0.1:3333/setup" -H "Content-Type: application/json" -d '{"config":{"server_address":"10.60.39.1","flag_regex":"[A-Z0-9]{31}=","auth_required":false},"accounts":{"a": "b"}}'

.PHONY: caronte-service
caronte-service:
	curl -X PUT "http://127.0.0.1:3333/api/services" \
			-H "Content-Type: application/json" \
			-d '{"port":3000,"name":"CCForms1","color":"#00897b","notes":""}'
	curl -X PUT "http://127.0.0.1:3333/api/services" \
			-H "Content-Type: application/json" \
			-d '{"port":3001,"name":"CCForms2","color":"#43a047","notes":""}'
	curl -X PUT "http://127.0.0.1:3333/api/services" \
	-H "Content-Type: application/json" \
	-d '{"port":2222,"name":"CookingNonna","color":"#e53935","notes":""}'
	curl -X PUT "http://127.0.0.1:3333/api/services" \
	-H "Content-Type: application/json" \
	-d '{"port":8000,"name":"exCCel","color":"#9e9d24","notes":""}'

.PHONY: caronte-upload-20250620
caronte-upload-20250620:
	cd /run/media/ironlanderl/prefixes/dev/caronte/newCaps/20250620/pcaps; \
	for file in *.pcap; do curl -X POST "http://127.0.0.1:3333/api/pcap/upload" -H "Content-Type: multipart/form-data" -F "file=@$$file" -F "flush_all=true"; done

.PHONY: caronte-upload-20250621
caronte-upload-20250621:
	cd /run/media/ironlanderl/prefixes/dev/caronte/newCaps/20250621/pcaps; \
	for file in *.pcap; do curl -X POST "http://127.0.0.1:3333/api/pcap/upload" -H "Content-Type: multipart/form-data" -F "file=@$$file" -F "flush_all=true"; done

.PHONY: caronte-upload-20260619
caronte-upload-20260619:
	cd /run/media/ironlanderl/prefixes/dev/caronte/newCaps/20260619/pcaps; \
	for file in *.pcapng; do curl -X POST "http://127.0.0.1:3333/api/pcap/upload" -H "Content-Type: multipart/form-data" -F "file=@$$file" -F "flush_all=true"; done

.PHONY: caronte-upload-20260620
caronte-upload-20260620:
	cd /run/media/ironlanderl/prefixes/dev/caronte/newCaps/20260620/pcaps; \
	for file in *.pcapng; do curl -X POST "http://127.0.0.1:3333/api/pcap/upload" -H "Content-Type: multipart/form-data" -F "file=@$$file" -F "flush_all=true"; done

#http://127.0.0.1:3333/api/connections?matched_rules=6ae216420000000000000001&service_port=3001&limit=-1
