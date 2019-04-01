#include <bits/stdc++.h>
#define vec(a) vector<a>
#define vecp(a,b) vector < pair< a, b > > 
#define pb push_back
#define minpq priority_queue <long long int, vector<long long int>, greater<long long int> > pq;
#define f(i,a,b) for(long long int i=a;i<b;i++)
#define fr(i,a,b) for(long long int i=a;i>=b;i--)
#define tc long long int t; cin>>t; while(t--)
#define mp make_pair
#define mapp(a,b) map<a, b>
#define umapp(a,b) unordered_map<a ,b> 
#define mem(d,val) memset(d,val,sizeof(d))
using namespace std;
#define mod 1000000007 
typedef long long int ll;

int main()
{
  ll n,m;
  cin>>n>>m;
  vecp(ll,ll) v;
  f(i,0,n)
  {
    ll a,b;
    cin>>a>>b;
    v.pb(mp(b,a));
  }
  ll sum=0,ans=INT_MIN;
  priority_queue <int, vector<int>, greater<int> > pq;
  sort(v.begin(),v.end());
  for(int i=n-1;i>=0;i--)
  {
    pq.push(v[i].second);
    sum+=v[i].second;
    if(pq.size()>m)
    {
      sum -= pq.top();
      pq.pop();
    }
    ans = max(ans,v[i].first*sum);

  }
  cout<<ans;
}