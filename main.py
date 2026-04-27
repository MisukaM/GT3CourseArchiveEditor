#GT3CourseArchiveEditor
import os
import struct
import argparse

print("GT3CourseArchiveEditor - Made by Misuka")

course_archive_header_size = 192 #192 byte header for crs archives

#db of filenames to use for outputted files
archive_filename_table = {
1: "01_MainCourseModel.mdl", 2: "02_MainCourseVisionList.lv", 3: "03_LODCourseVisionList.lv", 4: "04_CarReflectionVisionList.lv", 5: "05_CarReflectionModel.mdl", 6: "06_CourseReflectionVisionList.lv", 7: "07_ExtraCourseVisionList.lv",
9: "08_RoadSurfaceModel.mdl", 10: "09_RoadSurfaceVisionList.lv", 13: "10_RoadSurfaceModel2.mdl", 14: "11_RoadSurfaceVisionList2.lv", 21: "12_SkyboxModel.mdl", 22: "13_CourseBackgroundModel.mdl", 23: "14_CarReflectionModel2.mdl", 
24: "15_LODSkyboxModel.mdl", 25: "16_UnknownNightCourseFlag.bin", 26: "17_SmokeTexture.img", 27: "18_ExtraCourseModel.mdl", 28: "19_CourseRunwayData.rwy", 29: "20_CourseLightFlareData.gtfx", 30: "21_BillboardData.blbd", 31: "22_DrivingLines.ad", 32: "23_EnvironmentParameters.envptr",
33: "24_CourseMiniMapData.map", 34: "25_CourseReplayCameras.cam", 35: "26_CourseSoundData.crss", 36: "27_GadgetModels.mdl", 37: "28_AIParamRWD.bin", 38: "29_AIParamFWD.bin", 39: "30_AIParam4WD.bin",
40: "31_AIParamGTR.bin", 41: "32_CameraFile1.cam", 42: "33_CameraFile2.cam", 43: "34_UnknownCourseModel2.mdl"
}

#program functions

def count_files(course):
    last_file = 0
    try:
        with open(course, 'rb') as f:
            position_in_file = 0
            last_file = 0
            while position_in_file < course_archive_header_size:
                f.seek(position_in_file)
                read_data = struct.unpack('<I', f.read(4))
                if read_data[0] == 0:
                    position_in_file += 4
                else:
                    last_file += 1
                    position_in_file += 4
    except:
        print("File counting: Could not find course file.")
    return last_file

def count_files_in_dir(dir):
    file_count_in_dir = 0
    for path in os.listdir(dir):
        if os.path.isfile(os.path.join(dir, path)):
            file_count_in_dir += 1
    return file_count_in_dir

def find_next_pointer(position, initial_pointer, course):
    with open(course, 'rb') as f:
        secondary_position_in_file = position + 4
        file_length = 0
        while True:
            f.seek(secondary_position_in_file)
            read_data = struct.unpack('<I', f.read(4))
            if secondary_position_in_file == course_archive_header_size:
                file_length = 0
                return file_length
            if read_data[0] == 0:
                secondary_position_in_file += 4
                continue
            else:
                file_length = read_data[0] - initial_pointer
                return file_length

def dump_found_archive_files(course, start_pointer, end_pointer, output_folder, output_filename):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    with open(course, 'rb') as f:
        f.seek(start_pointer, 0)

        read_data = f.read(end_pointer - start_pointer)

        output_file_path = os.path.join(output_folder, output_filename)

        with open(output_file_path, 'wb') as output_file:
            output_file.write(read_data)
        print(f'Dumped data to "{output_file_path}"')
                
def crs_unpack(course):
    try:
        with open(course, 'rb') as f:
            position_in_file = 0
            dictionary_index = 0
            file_length = 0
            while position_in_file < course_archive_header_size:
                f.seek(position_in_file)
                read_data = struct.unpack('<I', f.read(4))
                dictionary_index = position_in_file // 4
                if read_data[0] == 0:
                    print(f"{'offset':<10}{'index':<8}")
                    print(f"{read_data[0]:<10}{dictionary_index:<8}\n")
                    print("_"*80)
                    position_in_file += 4
                else:
                    file_length = find_next_pointer(position_in_file, read_data[0], course)
                    if file_length == 0: #seek to the end of file and get datasize, if processing the last file in the archive (file length is 0 if processing last file)
                        f.seek(read_data[0])
                        end_of_file_reading = f.read()
                        file_length = len(end_of_file_reading)
                    print(f"{'offset':<10}{'filetype':<30}{'index':<8}{'datasize':<10}")
                    print(f"{read_data[0]:<10}{archive_filename_table[dictionary_index]:<30}{dictionary_index:<8}{file_length}{' bytes'}\n")
                    #dump file:
                    dump_found_archive_files(course, read_data[0], read_data[0] + file_length, course+"_out", archive_filename_table[dictionary_index])
                    print("_"*80)
                    position_in_file += 4

    except FileNotFoundError as e:
        print(f"Course unpacking: Could not find course file. Error: {e}")
    except struct.error as e:
        print(f"Struct unpacking error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during unpacking. {e}")

def crs_repack(course):
    offset = 0
    current_file_size = 0
    try:
        course_files = os.listdir(course+"_out")
        print("Files found:", len(course_files))
        print()

        with open(course, "wb") as f:
            f.write(b'\x00' * course_archive_header_size) #write header bytes
            offset = course_archive_header_size

        with open(course, "rb+") as f:
            for key, value in archive_filename_table.items():
                if value not in course_files:
                    print(f"Skipping missing file: {value}")
                    continue

                f.seek(key*4)
                offset_hex = struct.pack('<I', offset)
                f.write(offset_hex)
                with open(os.path.join(course + "_out", value), "rb") as openfile:
                    current_file_size = os.path.getsize(os.path.join(course + "_out", value))
                    read_data = openfile.read()
                    f.seek(offset)
                    f.write(read_data)
                    offset += current_file_size
        print()
        print("If files were skipped, this is normal, as not every course uses every file slot.")
        print()
        print(f'Course repacked successfully into "{course}"')
        print()
    
    except FileNotFoundError as e:
        print(f"Course repacking: Could not find course files. Error: {e}")
    except struct.error as e:
        print(f"Struct unpacking error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during repacking: {e}")


if __name__ == "__main__":
    current_dir = os.getcwd()
    file_count_in_dir = count_files_in_dir(current_dir)

    parser = argparse.ArgumentParser(description="GT3 Course Archive Unpacker/Rebuilder")
    parser.add_argument("--build", metavar="FILE", help="Rebuild course archive")
    parser.add_argument("--unpack", metavar="FILE", help="Unpacks course archive")
    parser.add_argument("--buildall", action="store_true", help="Builds all course files in the directory")
    parser.add_argument("--unpackall", action="store_true", help="Unpacks all course files in the directory")
    parser.add_argument("--exit", action="store_true", help="Exits the program")
    args = parser.parse_args()

    if args.build:
        crs_repack(args.build.removesuffix("_out"))

    elif args.unpack:
        file_count = count_files(args.unpack)
        print("Files found:", file_count)
        print()
        crs_unpack(args.unpack)
        
    elif args.buildall:
        for file in os.listdir(current_dir):
            if os.path.isdir(file) and file.endswith("_out"):
                selected_course = os.fsdecode(file)[:-4]
                print()
                crs_repack(selected_course)

    elif args.unpackall:
        for file in os.listdir(current_dir):
            if os.path.isfile(file):
                selected_course = os.fsdecode(file)
                file_count = count_files(selected_course)
                print("Files found:", file_count)
                print()
                crs_unpack(selected_course)

    elif args.exit:
        exit()

    else:
        parser.print_help()

    #main()
