
#include<iostream>

using namespace std;

void count_special_substrings(string S) {
	char c= S[0];
	int count=0, ans=0, N=S.length();

	for (int i=0;i<N;i++)
	{
		if(S[i]==c)
		{
			count+=1;
		}
	    else
	     {	     
		     ans += (count*(count+1))/2;
		     count = 1;
		     c = S[i];

		     for(int j=i+1,k=i-1;j<N,k>=0;j++,k--)
		     {	 if(S[j]==S[k])
				{
					ans+=1;
				}
		     		else break;
		     }

		}
	}
	ans += (count*(count+1))/2;
	cout<<ans;
	
}

int main(){
    string S;
    cin >> S;
    count_special_substrings(S);
    
    return 0;
}

