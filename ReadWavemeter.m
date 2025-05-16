FastWavemeterClient.dropAll()
alarm_t = 4;
ts = linspace(0, 1, 8192);
ts = repmat(ts, [1, alarm_t]);
Fviolet = 1600;
Fblue = 1300;
Fyellow = 400;
FIR = 350;

valsViolet = sin(2 * pi * Fviolet * ts); 
valsBlue = sin(2 * pi * Fblue * ts); 
valsYellow = sin(2 * pi * Fyellow * ts);
valsIR = sin(2 * pi * FIR * ts);

client = FastWavemeterClient.get('tcp://128.103.90.47:8850');

bAbort = 0;
%% reference D1
freq810 = 366162.660; %645; %650; %683;%366219.722;
range810 = 0.008;

freq589 = 508848.474; %450; %463;%508848.693;
range589 = 0.02;

freq1062 = 282286.060; %50;
range1062 = 0.01;
%% reference 911
% freq810 = 366162.660;%366219.722;
% range810 = 0.008;
% 
% freq589 = 508848.475;%508848.693;
% range589 = 0.02;
% 
% freq1062 = 282286.060;
% range1062 = 0.01;
while true
[freqs, times] = client.get_frequencies();

[~,idx810] = min(abs(freqs-freq810));
currentfreq810 = freqs(idx810);

[~,idx589] = min(abs(freqs-freq589));
currentfreq589 = freqs(idx589);

[~,idx1062] = min(abs(freqs-freq1062));
currentfreq1062 = freqs(idx1062);

%     if abs(currentfreq810-freq810)>range810
%         fprintf('Violet laser unlocked!');
%         soundsc(valsViolet);
%         PauseRunSeq;
%         if bAbort
%             AbortRunSeq;            
%         end
%         break
%     end
%     if abs(currentfreq589-freq589)>range589
%         fprintf('Yellow laser unlocked!');
%         soundsc(valsYellow);
%         PauseRunSeq;
%         if bAbort
%             AbortRunSeq;            
%         end
%         break
%     end
    fprintf('Cs IR laser freq %.3f ',currentfreq1062)

%     fprintf('Violet laser freq %.3f,yellow laser freq %.3f \n',currentfreq810,currentfreq589)
    if abs(currentfreq1062-freq1062)>range1062
        fprintf('IR laser unlocked!');
        soundsc(valsIR);
        PauseRunSeq;
        if bAbort
            AbortRunSeq;            
        end
        break
    end
    pause(1.5);
    disp(datestr(now, 'yyyy-mm-dd HH:MM:SS.FFF'))

end 
%%
% %%
% while true
%     date_str = datestr(datetime('now'), 'yyyymmdd');
%     wm = Wavemeter.get([date_str, '_fast_wm.csv'], 366270, 366272);
%     [~, f] = wm.ReadWavemeterNow(30);
%     fprintf('\n');
%    if mean(f) < 366270.615 || mean(f) > 366270.625
%         fprintf('Violet laser unlocked!');
%       % soundsc(valsBlue);
%         PauseRunSeq;
%         break
%    end
%     
%    
%     wm = Wavemeter.get([date_str, '_fast_wm.csv'], 508847, 508848.6);
%     [~, f] = wm.ReadWavemeterNow(30);
%     fprintf('\n');
%    if mean(f) < 508848.41|| mean(f) > 508848.44
%         fprintf('yellow laser unlocked!');
%       % soundsc(valsBlue);
%         PauseRunSeq;
%         break
%     end
%     pause(5);
% end
%%
% FastWavemeterClient.dropAll()
% client = FastWavemeterClient.get('tcp://128.103.90.47:8850');
% %%
% while true
% [freqs, times] = client.get_frequencies();
% currenttime = datetime(datestr(now));
%     thistime = times(16);
%     freqtime = datetime(thistime{1},'InputFormat','yyyy-MM-dd''T''HH:mm:ss.SSS');
%     currenttime = datetime(datestr(now));
%     gap = seconds(freqtime-currenttime)
%     pause(1)
% end