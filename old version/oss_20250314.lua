-- version: 20250314

local upload = require "resty.upload"
local str = require "resty.string"

local args = {}

--解析文件名
function get_filename(res)
    local filename = ngx.re.match(res,'(.+)filename="(.+)"(.*)')
    if filename then
        ngx.log(ngx.INFO, "file name : ", filename[2])
        return filename[2]
    end
end

--解析fieldName
function get_fieldname(res)
    local fieldname = ngx.re.match(res,'(.+)name="(.+)"(.*)')
    if fieldname then
        return fieldname[2]
    end
end

--解析post请求，并将解析结果存入args
function handle_uploading()
    local chunk_size = 5*1024
    --创建解析post请求的form对象
    local form, err = upload:new(chunk_size)
    if not form then
        ngx.status = ngx.HTTP_INTERNAL_SERVER_ERROR
        ngx.log(ngx.ERR, "failed to new upload: ", err)
        ngx.say("failed to new upload")
        return ngx.exit(500)
    end
    --设置读超时时间
    form:set_timeout(60000)

    local file_name = nil
    local file_exist = nil
    local filedata = {}
    local field_name = nil
    while true do
        local typ, res, err = form:read()
        --处理解析异常
        if not typ then
             ngx.status = ngx.HTTP_INTERNAL_SERVER_ERROR
             ngx.log(ngx.ERR, "parse post form error,format error:",err)
             ngx.say("failed to read: ", err)
             return ngx.exit(500)
        end
        --处理请求头
        if typ == "header" then
            file_name = get_filename(res[2])
            if file_name then
                file_exist = true
            end
	    if field_name == nil then 
                field_name = get_fieldname(res[2])
	    end
         --处理请求体
         elseif typ == "body" then
            if file_exist then
		table.insert(filedata, res)
            elseif field_name then 
               args[field_name] = res
               ngx.log(ngx.INFO, "field,",field_name,":",res)
            end
        --处理multipart end
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
        --结束跳出循环
        elseif typ == "eof" then
            break

        else
            -- do nothing
        end
    end
end

--创建发起put请求的httpClient
local httpc = require("resty.http").new()
httpc:set_timeout(60000)

local method = ngx.req.get_method()
--只处理POST请求
if  method == "POST" then
    handle_uploading()
    local putUrl = args["putUrl"]
    if  putUrl and args["filedata"] then 
        local  forward_url = ngx.decode_base64(putUrl)
        ngx.log(ngx.INFO, "putUrl : ", forward_url)
        --发起put请求
        local res, err = httpc:request_uri(forward_url, {
            method = "PUT",
            ssl_verify  = false,
            body = args["filedata"]
        })
        --处理服务器未响应异常
        if not res then
            ngx.status = ngx.HTTP_INTERNAL_SERVER_ERROR
            ngx.log(ngx.ERR, "request failed: ", err)
            ngx.say("pub request failed")
            return ngx.exit(500)
        end
        --处理服务器返回
        ngx.log(ngx.INFO, "reponse body : ", res.body)
        local resMsg = res.body
        ngx.header["Content-Length"] = #resMsg + 1
        ngx.say(res.body)

    end 
else  
    --处理GET方法
    ngx.status = ngx.HTTP_INTERNAL_SERVER_ERROR
    ngx.say("only support POST request")
    return ngx.exit(500)
end
