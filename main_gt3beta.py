#GT3CourseArchiveEditor
import os
import struct
import time

print("GT3BetaCourseArchiveEditor - Made by Misuka")

course_archive_header_size = 128 #128 byte header for crs archives

#db of filenames to use for outputted files
archive_filename_table = {
1: "01_CourseRunwayData", 2: "02_UnknownReplayData", 3: "03_CourseParameters", 5: "04_EnvironmentParameters", 6: "05_SkyboxModel", 7: "06_UnknownModel", 8: "07_MainCourseModel",
9: "08_CarReflectionModel2", 10: "09_CarReflectionModel", 11: "10_CourseReplayCameras", 12: "11_MainCourseVisualizer", 13: "12_BillboardData", 14: "13_CourseMapData",
15: "14_CarReflectionVisualizer", 16: "15_RoadSurfaceModel", 17: "16_RoadSurfaceModel2", 18: "17_LODCourseVisualizer", 19: "18_LODCourseVisualizer2", 20: "19_CourseLightFlareData"
}

archive_filename_table_gt3_final = {
1: "19_CourseRunwayData.rwy", 2: "02_UnknownReplayData", 3: "22_DrivingLines.ad", 5: "23_EnvironmentParameters.envptr", 6: "12_SkyboxModel.mdl", 7: "06_UnknownModel", 8: "01_MainCourseModel.mdl",
9: "14_CarReflectionModel2.mdl", 10: "05_CarReflectionModel.mdl", 11: "25_CourseReplayCameras.cam", 12: "02_MainCourseVisionList.lv", 13: "21_BillboardData.blbd", 14: "24_CourseMiniMapData.map",
15: "04_CarReflectionVisionList.lv", 16: "08_RoadSurfaceModel.mdl", 17: "10_RoadSurfaceModel2.mdl", 18: "03_LODCourseVisionList.lv", 19: "18_LODCourseVisualizer2", 20: "20_CourseLightFlareData.gtfx"
}

selected_archive = {}

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
                    print(f"{read_data[0]:<10}{selected_archive[dictionary_index]:<30}{dictionary_index:<8}{file_length}{' bytes'}\n")
                    #dump file:
                    dump_found_archive_files(course, read_data[0], read_data[0] + file_length, course+"_out", selected_archive[dictionary_index])
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

        with open(course+"_new", "wb") as f:
            f.write(b'\x00' * course_archive_header_size) #write header bytes
            offset = course_archive_header_size

        with open(course+"_new", "rb+") as f:
            for key, value in selected_archive.items():
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
        print("This is normal, not every course archive uses every file slot.")
        print()
        print(f'Course repacked successfully into "{course}_new"')
        print()
    
    except FileNotFoundError as e:
        print(f"Course repacking: Could not find course files. Error: {e}")
    except struct.error as e:
        print(f"Struct unpacking error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during repacking: {e}")

#user action
def main():
    while True:
        print()
        use_gt3_final_filenames = input('Use GT3 final filenames? Y/N: ')
        if use_gt3_final_filenames.lower() == "y":
            selected_archive = archive_filename_table_gt3_final
        elif use_gt3_final_filenames.lower() == "n":
            selected_archive = archive_filename_table
        else:
            print("Invalid command.")
        user_command = input('Choose action: "B"=Build, "U"=Unpack, "E"=Exit: ')
        if user_command.lower() == "e":
            print("Exiting...")
            time.sleep(1.5)
            break
        elif user_command.lower() == "b":
            selected_course = input("Input course filename: ")
            print()
            crs_repack(selected_course)
        elif user_command.lower() == "u":
            selected_course = input("Input course filename: ")
            file_count = count_files(selected_course)
            print("Files found:", file_count)
            print()
            crs_unpack(selected_course)
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()