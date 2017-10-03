#include <iostream>
#include <fstream>
#include <cstdio>
#include <string>

using namespace std;

int read_only_images(const char* img_file, const char* evt_file, const char* new_img_file, const char* new_evt_file){

	string img;
	string evt;

	string empty("");
	string cmp("{{");

	int nevent=0;
	int nimg=0;
	int nbrace=0;

	ifstream in_img_file(img_file);
	ifstream in_evt_file(evt_file);
	ofstream out_img_file(new_img_file);
	ofstream out_evt_file(new_evt_file);

	if ((in_img_file.is_open() && out_img_file.is_open()) && (in_evt_file.is_open() && out_evt_file.is_open())){
		while (getline(in_img_file, img)){
			if (img.size() > 1000){
				out_img_file << img << endl;
				nevent++;
			}	
		}
		while (getline(in_evt_file, evt)){
			if (evt.size() > 50){
				//cout << evt[1] << endl;
				
				if (evt[1] == '{'){
					evt.replace(0,1,empty);
					nbrace++;
					cout << evt << endl;
				}
				out_evt_file << evt << endl;
				nimg++;
			}
		}	
	}

        in_img_file.close();
        in_evt_file.close();
        out_img_file.close();
        out_evt_file.close();
	
	if (nevent != nimg){
		cout << "Different number of images and info_lines: " << nimg << " images and " << nevent << " events, quit." << endl;
		return -1;
	}
	
	else {
		cout << "Same number of images and info_lines: " << nevent << endl;
		cout << nbrace << " double braces replaced." << endl; 
		return 0;
	}
}
