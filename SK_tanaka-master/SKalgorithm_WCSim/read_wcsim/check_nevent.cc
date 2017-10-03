#include <iostream>
#include <fstream>
#include <cstdio>
#include <string>

using namespace std;

int check_nevent(const char* img_file, const char* evt_file){

	string img;
	string evt;

	string empty("");
	string cmp("{{");

	int nevent=0;
	int nimg=0;
	int nbrace=0;

	ifstream in_img_file(img_file);
	ifstream in_evt_file(evt_file);

	if (in_img_file.is_open() && in_evt_file.is_open()){
		while (getline(in_img_file, img)){
			if (img.size() > 1000){
				nevent++;
			}	
		}
		while (getline(in_evt_file, evt)){
			if (evt[1] == '{'){
				cout << "Double braces seen." << endl;
				return -1;
			}
			nimg++;
			
			if (evt.size() < 100) {
				cout << "What is this line.. investivate further" << endl;
				return -1;
			}
		}	
	}

        in_img_file.close();
        in_evt_file.close();
	
	if (nevent != nimg){
		cout << "Different number of images and info_lines: " << nimg << " images and " << nevent << " events, quit." << endl;
		return -1;
	}
	
	else {
		cout << "Same number of images and info_lines: " << nevent << endl;
		return 0;
	}
}
