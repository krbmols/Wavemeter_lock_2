x=importdata("Data Log 8.12.21.csv");

%setting up size of channels, and references from starting code
[number_of_rows,~]=size(x);
threshold=3000; %gHz

refFrequencies=[351679,714290]; %frequencies are measured in gigahertz 



channelOne_freqs=zeros(number_of_rows,1);
channelOne_times=zeros(number_of_rows,1);
channelTwo_freqs=zeros(number_of_rows,1);
channelTwo_times=zeros(number_of_rows,1);

%now to sort the values into their respective targets, for every value
%checked, its going to compare itself against the possible frequencies: if
%its close to one, add the time measurement and frequencies to a channels
%respective frequencies
disp(x(1,2))
for value=1:number_of_rows
    for reference=1:2
        difference=x(value,2)-refFrequencies(reference);
        if (0<abs(difference))&&(abs(difference)<threshold)
            if reference==1
                channelOne_freqs(value)=x(value,2);
                channelOne_times(value)=x(value,1);
            elseif reference==2
                channelTwo_freqs(value)=x(value,2);
                channelTwo_times(value)=x(value,1);
            else
                continue
            
            end
        else
            continue
                    
        end
        
        
        
    end 
end 



%resizing the arrays to properly account for only actual data
%loop through only in the case of the times
%v=find(channelTwo_freqs);
%channelTwo_freqs=channelTwo_freqs(v);
%channelTwo_times=channelTwo_times(v);


y=find(channelOne_freqs);
channelOne_freqs=channelOne_freqs(y);
channelOne_times=channelOne_times(y);

%setting up the plot window

figure(1)
subplot(2,1,1)
scatter(channelOne_times,channelOne_freqs,"r")
title("Time vs. Frequency Channel One")
xlabel("Seconds since start of Wavemeter Launch")
xlim([0,1000])
ylabel("Frequency(gHz)")


%subplot(2,1,2)
%plot(channelTwo_times,channelTwo_freqs,"b")
%title("Time vs. Frequency Channel Two")
%xlabel("Seconds since start of wavemeter launch")
%ylabel("Frequency(gHz)")


