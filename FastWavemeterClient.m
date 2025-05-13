%% wrapper for AnalysisClient.py

classdef FastWavemeterClient < handle
    properties
        client;
    end

    methods(Access = private)
        function self = FastWavemeterClient(url)
            [path, ~, ~] = fileparts(mfilename('fullpath'));
            pyglob = py.dict(pyargs('mat_srcpath', path, 'url', url));
            try
                py.exec('from Client import Client', pyglob);
            catch
                py.exec('import sys; sys.path.append(mat_srcpath)', pyglob);
                py.exec('from Client import Client', pyglob);
            end
            self.client = py.eval('Client(url)', pyglob);
        end
    end
    methods
        function [freqs, times] = get_frequencies(self)
            result = self.client.send_get_frequencies();
            temp_freqs = result{1};
            times = cell(result{2});
            times = cellfun(@(x) char(x), times, 'UniformOutput', false);
            temp_freqs = cell(temp_freqs.tolist());
            freqs = cellfun(@(x) x, temp_freqs);
        end
        function recreate_sock(self)
            self.client.recreate_sock();
        end
        function cleanup = register_cleanup(self)
            cleanup = FacyOnCleanup(@recreate_sock, self);
        end
    end

    properties(Constant, Access=private)
        cache = containers.Map();
    end
    methods(Static)
        function dropAll()
            remove(FastWavemeterClient.cache, keys(FastWavemeterClient.cache));
        end
        function res = get(url)
            cache = FastWavemeterClient.cache;
            if isKey(cache, url)
                res = cache(url);
                if ~isempty(res) && isvalid(res)
                    return;
                end
            end
            res = FastWavemeterClient(url);
            cache(url) = res;
        end
    end
end