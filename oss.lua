local upload = require "resty.upload"
local str = require "resty.string"

local args = {}

function get_filename(res)
    local filename = ngx.re.match(res,'(.+)filename="(.+)"(.*)')
    if filename then
        ngx.log(ngx.INFO, "file name : ", filename[2])
        return filename[2]
    end
end

function get_fieldname(res)
    local fieldname = ngx.re.match(res,'(.+)name="(.+)"(.*)')
    if fieldname then
        return fieldname[2]
    end
end

function handle_uploading()
    local chunk_size = 5*1024*1024
    local form, err = upload:new(chunk_size)
    if not form then
        ngx.log(ngx.ERR, "failed to new upload: ", err)
        ngx.exit(500)
    end

    form:set_timeout(6000)

    file_name = nil
    file_exist = nil
    filedata = {}
    field_name = nil
    while true do
        local typ, res, err = form:read()
        if not typ then
             ngx.say("failed to read: ", err)
             return
        end

        if typ == "header" then
            file_name = get_filename(res[2])
            if file_name then
                file_exist = true
            end
	    if field_name == nil then 
                field_name = get_fieldname(res[2])
	    end

         elseif typ == "body" then
            if file_exist then
		table.insert(filedata, res)
            elseif field_name then 
               args[field_name] = res
            end

        elseif typ == "part_end" then
            if file_exist then
		args["filedata"] = table.concat(filedata)
                file_exist = nil
		file_name = nil
		filedata = {}
            end
	    if field_name then
		field_name = nil
	     end

        elseif typ == "eof" then
            break

        else
            -- do nothing
        end
    end
end


local httpc = require("resty.http").new()
httpc:set_timeout(60000)
ok, err = httpc:set_keepalive(60000,512)


local method = ngx.req.get_method()
if  method == "POST" then
    handle_uploading()
    local putUrl = args["putUrl"]
    if  putUrl and args["filedata"] then 
        local  forward_url = ngx.decode_base64(putUrl)
        local res, err = httpc:request_uri(forward_url, {
            method = "PUT",
            ssl_verify  = false,
            body = args["filedata"]
        })
        if not res then
            ngx.status = 500
            ngx.log(ngx.ERR, "request failed: ", err)
            return
        end

        ngx.log(ngx.INFO, "reponse body : ", res.body)
        ngx.say(res.body)

    end 
else  
    ngx.status = 400
    ngx.say("only support POST request")
    ngx.exit(400)
end